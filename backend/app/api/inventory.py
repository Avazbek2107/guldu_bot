from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.deps import get_current_user, has_permission, technician_faculty_ids
from app.core.database import get_db
from app.models.enums import TechnicianFacultyRole, TicketStatus, UserRole
from app.models.faculty import Faculty
from app.models.inventory_item import InventoryItem
from app.models.technician_faculty_assignment import TechnicianFacultyAssignment
from app.models.technician_inventory_type_assignment import TechnicianInventoryTypeAssignment
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.inventory import (
    InventoryImportResult,
    InventoryImportSkip,
    InventoryItemCreate,
    InventoryItemOut,
    InventoryItemUpdate,
    RepairHistoryItem,
)
from app.services.inventory_excel import (
    faculty_location_label,
    generate_inventory_xlsx,
    parse_inventory_rows,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])

TECHNICIAN_ROLES = (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP)


async def _expand_with_kafedras(db: AsyncSession, faculty_ids: set[int]) -> set[int]:
    """A technician assigned to a top-level faculty/bo'lim also manages inventory
    recorded under that unit's kafedras, since kafedras don't get their own
    TechnicianFacultyAssignment rows."""
    if not faculty_ids:
        return faculty_ids
    kafedra_ids = (
        await db.execute(select(Faculty.id).where(Faculty.parent_id.in_(faculty_ids)))
    ).scalars().all()
    return faculty_ids | set(kafedra_ids)


async def _check_access(db: AsyncSession, current_user: User, faculty_id: int, action: str = "edit") -> None:
    if current_user.role == UserRole.SUPER_ADMIN:
        return
    if current_user.role == UserRole.ADMIN and has_permission(current_user, "inventory", action):
        return
    if current_user.role in TECHNICIAN_ROLES:
        allowed = await _expand_with_kafedras(db, technician_faculty_ids(current_user))
        if faculty_id in allowed:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")


async def _lookup_main_technician_id(db: AsyncSession, scope_faculty_id: int) -> int | None:
    result = await db.execute(
        select(TechnicianFacultyAssignment.user_id).where(
            TechnicianFacultyAssignment.faculty_id == scope_faculty_id,
            TechnicianFacultyAssignment.role == TechnicianFacultyRole.TECHNICIAN_MAIN,
        )
    )
    return result.scalar_one_or_none()


async def _lookup_category_technician_id(db: AsyncSession, inventory_type: str | None) -> int | None:
    """A technician can be the university-wide go-to person for an inventory
    TYPE (e.g. all Kamera/NVR units), independent of faculty — this takes
    priority over the faculty's own main technician when auto-assigning."""
    if not inventory_type:
        return None
    result = await db.execute(
        select(TechnicianInventoryTypeAssignment.user_id).where(
            TechnicianInventoryTypeAssignment.inventory_type == inventory_type
        )
    )
    return result.scalar_one_or_none()


async def _validate_assigned_technician(db: AsyncSession, technician_id: int | None, scope_faculty_id: int) -> None:
    if technician_id is None:
        return
    technician = await db.get(User, technician_id)
    if technician is None or technician.role not in TECHNICIAN_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Texnik xodim topilmadi")
    result = await db.execute(
        select(TechnicianFacultyAssignment.id).where(
            TechnicianFacultyAssignment.user_id == technician_id,
            TechnicianFacultyAssignment.faculty_id == scope_faculty_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Texnik xodim ushbu fakultet/bo'limga biriktirilmagan",
        )


def _to_out(
    item: InventoryItem,
    faculty_name: str,
    technician_name: str | None,
    repair_count: int,
    last_repaired_at,
) -> InventoryItemOut:
    return InventoryItemOut(
        id=item.id,
        faculty_id=item.faculty_id,
        faculty_name=faculty_name,
        room=item.room,
        inventory_number=item.inventory_number,
        uzasbo=item.uzasbo,
        inventory_type=item.inventory_type,
        model=item.model,
        status=item.status,
        internet_connection=item.internet_connection,
        mac_address=item.mac_address,
        responsible_person=item.responsible_person,
        assigned_technician_id=item.assigned_technician_id,
        assigned_technician_name=technician_name,
        repair_count=repair_count,
        last_repaired_at=last_repaired_at,
        created_at=item.created_at,
    )


async def _serialize_one(db: AsyncSession, item: InventoryItem, faculty_name: str) -> InventoryItemOut:
    stats = (
        await db.execute(
            select(func.count(Ticket.id), func.max(Ticket.closed_at)).where(
                Ticket.inventory_item_id == item.id, Ticket.status == TicketStatus.CLOSED
            )
        )
    ).one()
    technician_name = None
    if item.assigned_technician_id is not None:
        technician = await db.get(User, item.assigned_technician_id)
        technician_name = technician.full_name if technician is not None else None
    return _to_out(item, faculty_name, technician_name, stats[0] or 0, stats[1])


async def _faculty_location_name(db: AsyncSession, faculty: Faculty) -> str:
    if faculty.parent_id is None:
        return faculty.name
    parent = await db.get(Faculty, faculty.parent_id)
    return faculty_location_label(faculty.name, parent.name if parent else None)


async def _fetch_inventory(
    db: AsyncSession, current_user: User, faculty_id: int | None
) -> list[InventoryItemOut]:
    technician_alias = aliased(User)
    parent_alias = aliased(Faculty)
    query = (
        select(InventoryItem, Faculty.name, parent_alias.name, technician_alias.full_name)
        .join(Faculty, InventoryItem.faculty_id == Faculty.id)
        .outerjoin(parent_alias, Faculty.parent_id == parent_alias.id)
        .outerjoin(technician_alias, InventoryItem.assigned_technician_id == technician_alias.id)
    )

    if current_user.role == UserRole.SUPER_ADMIN or (
        current_user.role == UserRole.ADMIN and has_permission(current_user, "inventory", "view")
    ):
        if faculty_id is not None:
            query = query.where(InventoryItem.faculty_id == faculty_id)
    elif current_user.role in TECHNICIAN_ROLES:
        allowed = await _expand_with_kafedras(db, technician_faculty_ids(current_user))
        if not allowed:
            return []
        if faculty_id is not None:
            if faculty_id not in allowed:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")
            query = query.where(InventoryItem.faculty_id == faculty_id)
        else:
            query = query.where(InventoryItem.faculty_id.in_(allowed))
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")

    rows = (await db.execute(query.order_by(InventoryItem.id))).all()
    if not rows:
        return []

    item_ids = [item.id for item, _, _, _ in rows]
    repair_rows = (
        await db.execute(
            select(Ticket.inventory_item_id, func.count(Ticket.id), func.max(Ticket.closed_at))
            .where(Ticket.inventory_item_id.in_(item_ids), Ticket.status == TicketStatus.CLOSED)
            .group_by(Ticket.inventory_item_id)
        )
    ).all()
    repair_map = {r[0]: (r[1], r[2]) for r in repair_rows}

    return [
        _to_out(item, faculty_location_label(name, parent_name), technician_name, *repair_map.get(item.id, (0, None)))
        for item, name, parent_name, technician_name in rows
    ]


@router.get("", response_model=list[InventoryItemOut])
async def list_inventory(
    faculty_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _fetch_inventory(db, current_user, faculty_id)


@router.get("/export")
async def export_inventory(
    faculty_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = await _fetch_inventory(db, current_user, faculty_id)
    all_faculties = (await db.execute(select(Faculty))).scalars().all()
    by_id = {f.id: f for f in all_faculties}
    location_options = sorted(
        {
            faculty_location_label(f.name, by_id[f.parent_id].name if f.parent_id in by_id else None)
            for f in all_faculties
        }
    )
    content = generate_inventory_xlsx(items, location_options)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inventar.xlsx"},
    )


@router.post("/import", response_model=InventoryImportResult)
async def import_inventory(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.SUPER_ADMIN and not (
        current_user.role == UserRole.ADMIN and has_permission(current_user, "inventory", "create")
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")
    content = await file.read()
    try:
        rows = parse_inventory_rows(content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Fayl formatini o'qib bo'lmadi"
        ) from exc

    faculties = (await db.execute(select(Faculty))).scalars().all()
    by_id = {f.id: f for f in faculties}
    faculty_by_label = {
        faculty_location_label(f.name, by_id[f.parent_id].name if f.parent_id in by_id else None)
        .strip()
        .lower(): f
        for f in faculties
    }

    main_tech_rows = (
        await db.execute(
            select(TechnicianFacultyAssignment.faculty_id, TechnicianFacultyAssignment.user_id).where(
                TechnicianFacultyAssignment.role == TechnicianFacultyRole.TECHNICIAN_MAIN
            )
        )
    ).all()
    main_technician_by_faculty = {faculty_id: user_id for faculty_id, user_id in main_tech_rows}

    category_tech_rows = (
        await db.execute(
            select(TechnicianInventoryTypeAssignment.inventory_type, TechnicianInventoryTypeAssignment.user_id)
        )
    ).all()
    category_technician_by_type = {inv_type: user_id for inv_type, user_id in category_tech_rows}

    created = 0
    skipped: list[InventoryImportSkip] = []
    for row in rows:
        faculty = faculty_by_label.get(row.location_label.strip().lower())
        if faculty is None:
            skipped.append(
                InventoryImportSkip(
                    row=row.row_number, reason=f"Fakultet/bo'lim topilmadi: '{row.location_label}'"
                )
            )
            continue
        scope_faculty_id = faculty.parent_id if faculty.parent_id is not None else faculty.id
        db.add(
            InventoryItem(
                faculty_id=faculty.id,
                room=row.room,
                inventory_number=row.inventory_number,
                uzasbo=row.uzasbo,
                inventory_type=row.inventory_type,
                model=row.model,
                status=row.status or "Ishchi",
                internet_connection=row.internet_connection,
                mac_address=row.mac_address,
                responsible_person=row.responsible_person,
                assigned_technician_id=(
                    category_technician_by_type.get(row.inventory_type)
                    or main_technician_by_faculty.get(scope_faculty_id)
                ),
            )
        )
        created += 1

    await db.commit()
    return InventoryImportResult(created=created, skipped=skipped)


@router.get("/{item_id}/history", response_model=list[RepairHistoryItem])
async def get_inventory_history(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await db.get(InventoryItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventar topilmadi")
    await _check_access(db, current_user, item.faculty_id, "view")

    technician_alias = aliased(User)
    rows = (
        await db.execute(
            select(Ticket, technician_alias.full_name)
            .outerjoin(technician_alias, Ticket.assigned_technician_id == technician_alias.id)
            .where(Ticket.inventory_item_id == item_id, Ticket.status == TicketStatus.CLOSED)
            .order_by(Ticket.closed_at.desc())
        )
    ).all()
    return [
        RepairHistoryItem(
            ticket_id=ticket.id,
            ticket_number=ticket.ticket_number,
            closed_at=ticket.closed_at,
            resolution_comment=ticket.resolution_comment,
            technician_full_name=tech_name,
            is_suspicious=ticket.is_suspicious,
        )
        for ticket, tech_name in rows
    ]


@router.post("", response_model=InventoryItemOut, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    payload: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _check_access(db, current_user, payload.faculty_id, "create")
    faculty = await db.get(Faculty, payload.faculty_id)
    if faculty is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fakultet/bo'lim topilmadi")
    scope_faculty_id = faculty.parent_id if faculty.parent_id is not None else faculty.id

    data = payload.model_dump()
    if data.get("assigned_technician_id") is None:
        data["assigned_technician_id"] = await _lookup_category_technician_id(
            db, data.get("inventory_type")
        ) or await _lookup_main_technician_id(db, scope_faculty_id)
    else:
        await _validate_assigned_technician(db, data["assigned_technician_id"], scope_faculty_id)

    item = InventoryItem(**data)
    db.add(item)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ma'lumotlar noto'g'ri") from exc
    await db.refresh(item)
    return await _serialize_one(db, item, await _faculty_location_name(db, faculty))


@router.patch("/{item_id}", response_model=InventoryItemOut)
async def update_inventory_item(
    item_id: int,
    payload: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await db.get(InventoryItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventar topilmadi")
    await _check_access(db, current_user, item.faculty_id)

    data = payload.model_dump(exclude_unset=True)
    target_faculty_id = data.get("faculty_id", item.faculty_id)
    target_faculty = None
    if target_faculty_id != item.faculty_id:
        await _check_access(db, current_user, target_faculty_id)
        target_faculty = await db.get(Faculty, target_faculty_id)
        if target_faculty is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fakultet/bo'lim topilmadi")
    else:
        target_faculty = await db.get(Faculty, target_faculty_id)
    scope_faculty_id = target_faculty.parent_id if target_faculty.parent_id is not None else target_faculty.id

    if "assigned_technician_id" in data:
        await _validate_assigned_technician(db, data["assigned_technician_id"], scope_faculty_id)
    elif target_faculty_id != item.faculty_id and item.assigned_technician_id is not None:
        # Faculty is changing but no new technician was specified — clear the
        # now-stale assignment rather than silently leaving a technician from
        # the OLD faculty attached to an item that no longer belongs to them.
        data["assigned_technician_id"] = None

    for field, value in data.items():
        setattr(item, field, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ma'lumotlar noto'g'ri") from exc
    await db.refresh(item)

    faculty = await db.get(Faculty, item.faculty_id)
    return await _serialize_one(db, item, await _faculty_location_name(db, faculty))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await db.get(InventoryItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventar topilmadi")
    await _check_access(db, current_user, item.faculty_id, "delete")
    await db.delete(item)
    await db.commit()
