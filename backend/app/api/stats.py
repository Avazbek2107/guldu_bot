from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission, technician_faculty_ids
from app.core.database import get_db
from app.models.enums import OrgUnitType, TicketStatus, UserRole
from app.models.faculty import Faculty
from app.models.inventory_item import InventoryItem
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.stats import (
    CategoryStat,
    DailyCount,
    DashboardStats,
    FacultyStat,
    InventoryFacultyStat,
    InventoryStatusStat,
    InventoryTypeStat,
    MyDashboardStats,
    ReporterStat,
    TechnicianInventoryStat,
    TechnicianInventoryTypeCount,
    TechnicianStat,
)

router = APIRouter(prefix="/stats", tags=["stats"])

TECHNICIAN_ROLES = (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP)

TREND_DAYS = 30
TOP_REPORTERS_LIMIT = 15

INVENTORY_STATUS_WORKING = "Ishchi"
INVENTORY_STATUS_NEEDS_REPAIR = "Ta'mir talab"
INVENTORY_STATUS_UNUSABLE = "Yaroqsiz"


def _technician_stat_from_rows(tech: User, rows: list[tuple]) -> TechnicianStat:
    accepted = len(rows)
    closed_rows = [r for r in rows if r[0] == TicketStatus.CLOSED]
    closed = len(closed_rows)
    open_remaining = accepted - closed
    close_durations_hours = [
        (r[2] - r[1]).total_seconds() / 3600 for r in closed_rows if r[1] is not None and r[2] is not None
    ]
    avg_close_hours = sum(close_durations_hours) / len(close_durations_hours) if close_durations_hours else None
    efficiency_percent = (closed / accepted * 100) if accepted > 0 else None

    return TechnicianStat(
        technician_id=tech.id,
        full_name=tech.full_name,
        accepted=accepted,
        closed=closed,
        open_remaining=open_remaining,
        avg_close_hours=avg_close_hours,
        efficiency_percent=efficiency_percent,
    )


@router.get("/dashboard", response_model=DashboardStats, dependencies=[Depends(require_permission("dashboard", "view"))])
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)

    status_counts = dict(
        (await db.execute(select(Ticket.status, func.count()).group_by(Ticket.status))).all()
    )
    total_tickets = sum(status_counts.values())
    open_tickets = status_counts.get(TicketStatus.OPEN, 0)
    in_progress_tickets = status_counts.get(TicketStatus.IN_PROGRESS, 0)
    closed_tickets = status_counts.get(TicketStatus.CLOSED, 0)

    # Kafedras (parent_id set) are academic sub-units nested under a faculty for
    # display purposes only — tickets/inventory are never filed directly against
    # one, so they're excluded here entirely rather than showing up as
    # zero-row noise. Faculty-type and standalone Department-type ("bo'lim")
    # units are kept in separate lists so they render as separate dashboard
    # tables instead of one merged one.
    org_units = (
        (await db.execute(select(Faculty).where(Faculty.parent_id.is_(None)))).scalars().all()
    )
    faculty_units = [f for f in org_units if f.unit_type == OrgUnitType.FACULTY]
    department_units = [f for f in org_units if f.unit_type == OrgUnitType.DEPARTMENT]

    # Shared faculty/kafedra rollup used by both the inventory-status and
    # inventory-type breakdowns below: a kafedra's items count toward its
    # parent faculty/bo'lim so "Fakultet va bo'limlar kesimida" filtering
    # always operates on the same top-level unit list as the rest of the page.
    all_faculties = (await db.execute(select(Faculty))).scalars().all()
    top_level_of: dict[int, int] = {f.id: (f.parent_id if f.parent_id is not None else f.id) for f in all_faculties}
    kafedras = [f for f in all_faculties if f.parent_id is not None]

    faculty_status_rows = (
        await db.execute(select(Ticket.faculty_id, Ticket.status, func.count()).group_by(Ticket.faculty_id, Ticket.status))
    ).all()
    faculty_counts: dict[int, dict[TicketStatus, int]] = defaultdict(dict)
    for faculty_id, ticket_status, count in faculty_status_rows:
        faculty_counts[faculty_id][ticket_status] = count

    def _build_faculty_stat(f: Faculty) -> FacultyStat:
        return FacultyStat(
            faculty_id=f.id,
            faculty_name=f.name,
            total=sum(faculty_counts.get(f.id, {}).values()),
            open=faculty_counts.get(f.id, {}).get(TicketStatus.OPEN, 0),
            in_progress=faculty_counts.get(f.id, {}).get(TicketStatus.IN_PROGRESS, 0),
            closed=faculty_counts.get(f.id, {}).get(TicketStatus.CLOSED, 0),
        )

    faculty_stats = [_build_faculty_stat(f) for f in faculty_units]
    department_stats = [_build_faculty_stat(f) for f in department_units]

    technicians = (
        await db.execute(select(User).where(User.role.in_([UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP])))
    ).scalars().all()
    assigned_tickets = (
        await db.execute(
            select(Ticket.assigned_technician_id, Ticket.status, Ticket.created_at, Ticket.closed_at).where(
                Ticket.assigned_technician_id.is_not(None)
            )
        )
    ).all()

    by_technician: dict[int, list] = defaultdict(list)
    for tech_id, t_status, created_at, closed_at in assigned_tickets:
        by_technician[tech_id].append((t_status, created_at, closed_at))

    technician_stats = [
        _technician_stat_from_rows(tech, by_technician.get(tech.id, [])) for tech in technicians
    ]

    reporter_rows = (
        await db.execute(
            select(
                Ticket.created_by_user_id,
                func.count().label("total"),
                func.sum(case((Ticket.status != TicketStatus.CLOSED, 1), else_=0)).label("open_count"),
                func.sum(case((Ticket.is_suspicious.is_(True), 1), else_=0)).label("suspicious_count"),
                func.max(Ticket.created_at).label("last_at"),
            )
            .group_by(Ticket.created_by_user_id)
            .order_by(func.count().desc())
            .limit(TOP_REPORTERS_LIMIT)
        )
    ).all()

    reporter_user_ids = [row.created_by_user_id for row in reporter_rows]
    reporter_users: dict[int, User] = {}
    if reporter_user_ids:
        reporter_users = {
            u.id: u
            for u in (await db.execute(select(User).where(User.id.in_(reporter_user_ids)))).scalars().all()
        }
    faculty_names = {f.id: f.name for f in org_units}

    reporter_stats = []
    for row in reporter_rows:
        user = reporter_users.get(row.created_by_user_id)
        if user is None:
            continue
        reporter_stats.append(
            ReporterStat(
                user_id=user.id,
                full_name=user.full_name,
                phone=user.phone,
                faculty_id=user.faculty_id,
                faculty_name=faculty_names.get(user.faculty_id) if user.faculty_id is not None else None,
                total_tickets=row.total,
                open_tickets=row.open_count,
                suspicious_tickets=row.suspicious_count,
                last_ticket_at=row.last_at,
            )
        )

    category_rows = (await db.execute(select(Ticket.category, func.count()).group_by(Ticket.category))).all()
    category_stats = [CategoryStat(category=cat.value, count=count) for cat, count in category_rows]

    suspicious_user_count = (
        await db.execute(select(func.count()).select_from(User).where(User.is_suspicious.is_(True)))
    ).scalar_one()
    blocked_user_count = (
        await db.execute(select(func.count()).select_from(User).where(User.is_blocked.is_(True)))
    ).scalar_one()

    trend_start = now - timedelta(days=TREND_DAYS)
    recent_created_ats = (
        await db.execute(select(Ticket.created_at).where(Ticket.created_at >= trend_start))
    ).scalars().all()
    day_counts = Counter(created_at.date().isoformat() for created_at in recent_created_ats)
    daily_trend = []
    for offset in range(TREND_DAYS, -1, -1):
        day = (now - timedelta(days=offset)).date().isoformat()
        daily_trend.append(DailyCount(date=day, count=day_counts.get(day, 0)))

    inventory_status_rows = (
        await db.execute(select(InventoryItem.status, func.count()).group_by(InventoryItem.status))
    ).all()
    total_inventory_items = sum(count for _, count in inventory_status_rows)
    inventory_status_stats = [InventoryStatusStat(status=st, count=count) for st, count in inventory_status_rows]

    # Cross-tabbed by top-level faculty/bo'lim (kafedra items roll up to their
    # parent, same as inventory_faculty_stats below) so the dashboard can offer
    # a "Fakultet va bo'limlar kesimida" filter on top of the type breakdown
    # without a second round-trip.
    unit_name_by_id = {f.id: f.name for f in org_units}
    inventory_type_rows = (
        await db.execute(
            select(InventoryItem.faculty_id, InventoryItem.inventory_type, func.count()).group_by(
                InventoryItem.faculty_id, InventoryItem.inventory_type
            )
        )
    ).all()
    inventory_type_counts: dict[int, dict[str, int]] = defaultdict(dict)
    for faculty_id, inv_type, count in inventory_type_rows:
        top_level_id = top_level_of.get(faculty_id, faculty_id)
        key = inv_type or "Belgilanmagan"
        inventory_type_counts[top_level_id][key] = inventory_type_counts[top_level_id].get(key, 0) + count

    inventory_type_stats = [
        InventoryTypeStat(faculty_id=unit_id, faculty_name=unit_name_by_id.get(unit_id, "Noma'lum"), inventory_type=t, count=c)
        for unit_id, counts in inventory_type_counts.items()
        for t, c in counts.items()
    ]

    # Inventory can be recorded directly against a kafedra. Each top-level
    # faculty/bo'lim row shows the rolled-up total (including its kafedras)
    # so nothing is silently dropped from the summary; kafedras are also
    # reported individually so the UI can expand a faculty row into its
    # per-kafedra breakdown.
    inventory_faculty_rows = (
        await db.execute(
            select(InventoryItem.faculty_id, InventoryItem.status, func.count()).group_by(
                InventoryItem.faculty_id, InventoryItem.status
            )
        )
    ).all()
    inventory_unit_counts: dict[int, dict[str, int]] = defaultdict(dict)
    inventory_faculty_counts: dict[int, dict[str, int]] = defaultdict(dict)
    for faculty_id, item_status, count in inventory_faculty_rows:
        inventory_unit_counts[faculty_id][item_status] = count
        top_level_id = top_level_of.get(faculty_id, faculty_id)
        inventory_faculty_counts[top_level_id][item_status] = (
            inventory_faculty_counts[top_level_id].get(item_status, 0) + count
        )

    def _build_inventory_stat(faculty_id: int, name: str, parent_id: int | None, counts: dict[str, int]) -> InventoryFacultyStat:
        return InventoryFacultyStat(
            faculty_id=faculty_id,
            faculty_name=name,
            parent_id=parent_id,
            total=sum(counts.values()),
            working=counts.get(INVENTORY_STATUS_WORKING, 0),
            needs_repair=counts.get(INVENTORY_STATUS_NEEDS_REPAIR, 0),
            unusable=counts.get(INVENTORY_STATUS_UNUSABLE, 0),
        )

    inventory_faculty_stats = [
        _build_inventory_stat(f.id, f.name, None, inventory_faculty_counts.get(f.id, {})) for f in org_units
    ] + [
        _build_inventory_stat(k.id, k.name, k.parent_id, inventory_unit_counts.get(k.id, {})) for k in kafedras
    ]

    technician_inventory_rows = (
        await db.execute(
            select(InventoryItem.assigned_technician_id, InventoryItem.inventory_type, func.count())
            .where(InventoryItem.assigned_technician_id.is_not(None))
            .group_by(InventoryItem.assigned_technician_id, InventoryItem.inventory_type)
        )
    ).all()
    technician_inventory_counts: dict[int, dict[str, int]] = defaultdict(dict)
    for tech_id, inv_type, count in technician_inventory_rows:
        technician_inventory_counts[tech_id][inv_type or "Belgilanmagan"] = count

    technician_inventory_stats = [
        TechnicianInventoryStat(
            technician_id=tech.id,
            technician_name=tech.full_name,
            total=sum(technician_inventory_counts.get(tech.id, {}).values()),
            by_type=[
                TechnicianInventoryTypeCount(inventory_type=t, count=c)
                for t, c in sorted(
                    technician_inventory_counts.get(tech.id, {}).items(), key=lambda item: -item[1]
                )
            ],
        )
        for tech in technicians
    ]
    technician_inventory_stats.sort(key=lambda s: -s.total)

    return DashboardStats(
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        closed_tickets=closed_tickets,
        faculty_stats=faculty_stats,
        department_stats=department_stats,
        technician_stats=technician_stats,
        reporter_stats=reporter_stats,
        category_stats=category_stats,
        suspicious_user_count=suspicious_user_count,
        blocked_user_count=blocked_user_count,
        daily_trend=daily_trend,
        total_inventory_items=total_inventory_items,
        inventory_status_stats=inventory_status_stats,
        inventory_type_stats=inventory_type_stats,
        inventory_faculty_stats=inventory_faculty_stats,
        technician_inventory_stats=technician_inventory_stats,
    )


@router.get("/me", response_model=MyDashboardStats)
async def get_my_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Technicians have no `dashboard` RBAC permission (that's admin-only), so
    # this doesn't go through require_permission — it's gated on role instead,
    # and deliberately scoped to the technician's own performance plus their
    # own assigned faculties, never university-wide reporter/technician data.
    if current_user.role not in TECHNICIAN_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")

    own_rows = (
        await db.execute(
            select(Ticket.status, Ticket.created_at, Ticket.closed_at).where(
                Ticket.assigned_technician_id == current_user.id
            )
        )
    ).all()
    my_stat = _technician_stat_from_rows(current_user, own_rows)

    own_faculty_ids = technician_faculty_ids(current_user)
    if not own_faculty_ids:
        return MyDashboardStats(my_stat=my_stat, faculty_stats=[], inventory_faculty_stats=[])

    all_faculties = (await db.execute(select(Faculty))).scalars().all()
    top_level_of: dict[int, int] = {f.id: (f.parent_id if f.parent_id is not None else f.id) for f in all_faculties}
    faculty_name_by_id = {f.id: f.name for f in all_faculties}

    # Roll assigned faculty/kafedra ids up to their top-level unit, then pull
    # in every faculty/kafedra sharing that top level so a technician assigned
    # to a kafedra still sees the parent faculty's aggregated totals — mirrors
    # the rollup already used for the university-wide dashboard above.
    own_top_level_ids = {top_level_of.get(fid, fid) for fid in own_faculty_ids}
    relevant_faculty_ids = [f.id for f in all_faculties if top_level_of.get(f.id, f.id) in own_top_level_ids]

    faculty_status_rows = (
        await db.execute(
            select(Ticket.faculty_id, Ticket.status, func.count())
            .where(Ticket.faculty_id.in_(relevant_faculty_ids))
            .group_by(Ticket.faculty_id, Ticket.status)
        )
    ).all()
    faculty_counts: dict[int, dict[TicketStatus, int]] = defaultdict(dict)
    for faculty_id, ticket_status, count in faculty_status_rows:
        top_level_id = top_level_of.get(faculty_id, faculty_id)
        faculty_counts[top_level_id][ticket_status] = faculty_counts[top_level_id].get(ticket_status, 0) + count

    faculty_stats = [
        FacultyStat(
            faculty_id=unit_id,
            faculty_name=faculty_name_by_id.get(unit_id, "Noma'lum"),
            total=sum(counts.values()),
            open=counts.get(TicketStatus.OPEN, 0),
            in_progress=counts.get(TicketStatus.IN_PROGRESS, 0),
            closed=counts.get(TicketStatus.CLOSED, 0),
        )
        for unit_id, counts in faculty_counts.items()
    ]

    inventory_rows = (
        await db.execute(
            select(InventoryItem.faculty_id, InventoryItem.status, func.count())
            .where(InventoryItem.faculty_id.in_(relevant_faculty_ids))
            .group_by(InventoryItem.faculty_id, InventoryItem.status)
        )
    ).all()
    inventory_counts: dict[int, dict[str, int]] = defaultdict(dict)
    for faculty_id, item_status, count in inventory_rows:
        top_level_id = top_level_of.get(faculty_id, faculty_id)
        inventory_counts[top_level_id][item_status] = inventory_counts[top_level_id].get(item_status, 0) + count

    inventory_faculty_stats = [
        InventoryFacultyStat(
            faculty_id=unit_id,
            faculty_name=faculty_name_by_id.get(unit_id, "Noma'lum"),
            total=sum(counts.values()),
            working=counts.get(INVENTORY_STATUS_WORKING, 0),
            needs_repair=counts.get(INVENTORY_STATUS_NEEDS_REPAIR, 0),
            unusable=counts.get(INVENTORY_STATUS_UNUSABLE, 0),
        )
        for unit_id, counts in inventory_counts.items()
    ]

    return MyDashboardStats(
        my_stat=my_stat,
        faculty_stats=faculty_stats,
        inventory_faculty_stats=inventory_faculty_stats,
    )
