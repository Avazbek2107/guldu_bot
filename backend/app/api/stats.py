from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.enums import TicketStatus, UserRole
from app.models.faculty import Faculty
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.stats import CategoryStat, DailyCount, DashboardStats, FacultyStat, ReporterStat, TechnicianStat

router = APIRouter(prefix="/stats", tags=["stats"])

TREND_DAYS = 30
TOP_REPORTERS_LIMIT = 15


@router.get("/dashboard", response_model=DashboardStats, dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))])
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    status_counts = dict(
        (await db.execute(select(Ticket.status, func.count()).group_by(Ticket.status))).all()
    )
    total_tickets = sum(status_counts.values())
    open_tickets = status_counts.get(TicketStatus.OPEN, 0)
    in_progress_tickets = status_counts.get(TicketStatus.IN_PROGRESS, 0)
    closed_tickets = status_counts.get(TicketStatus.CLOSED, 0)

    faculties = (await db.execute(select(Faculty))).scalars().all()
    faculty_status_rows = (
        await db.execute(select(Ticket.faculty_id, Ticket.status, func.count()).group_by(Ticket.faculty_id, Ticket.status))
    ).all()
    faculty_counts: dict[int, dict[TicketStatus, int]] = defaultdict(dict)
    for faculty_id, ticket_status, count in faculty_status_rows:
        faculty_counts[faculty_id][ticket_status] = count

    faculty_stats = [
        FacultyStat(
            faculty_id=f.id,
            faculty_name=f.name,
            total=sum(faculty_counts.get(f.id, {}).values()),
            open=faculty_counts.get(f.id, {}).get(TicketStatus.OPEN, 0),
            in_progress=faculty_counts.get(f.id, {}).get(TicketStatus.IN_PROGRESS, 0),
            closed=faculty_counts.get(f.id, {}).get(TicketStatus.CLOSED, 0),
        )
        for f in faculties
    ]

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

    technician_stats = []
    for tech in technicians:
        rows = by_technician.get(tech.id, [])
        accepted = len(rows)
        closed_rows = [r for r in rows if r[0] == TicketStatus.CLOSED]
        closed = len(closed_rows)
        open_remaining = accepted - closed
        close_durations_hours = [
            (r[2] - r[1]).total_seconds() / 3600 for r in closed_rows if r[1] is not None and r[2] is not None
        ]
        avg_close_hours = sum(close_durations_hours) / len(close_durations_hours) if close_durations_hours else None
        efficiency_percent = (closed / accepted * 100) if accepted > 0 else None

        technician_stats.append(
            TechnicianStat(
                technician_id=tech.id,
                full_name=tech.full_name,
                faculty_id=tech.faculty_id,
                accepted=accepted,
                closed=closed,
                open_remaining=open_remaining,
                avg_close_hours=avg_close_hours,
                efficiency_percent=efficiency_percent,
            )
        )

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
    faculty_names = {f.id: f.name for f in faculties}

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

    now = datetime.now(timezone.utc)

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

    return DashboardStats(
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        closed_tickets=closed_tickets,
        faculty_stats=faculty_stats,
        technician_stats=technician_stats,
        reporter_stats=reporter_stats,
        category_stats=category_stats,
        suspicious_user_count=suspicious_user_count,
        blocked_user_count=blocked_user_count,
        daily_trend=daily_trend,
    )
