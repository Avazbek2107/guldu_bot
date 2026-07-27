from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.deps import get_current_user, has_permission, technician_faculty_ids
from app.core.database import get_db
from app.models.enums import TechnicianFacultyRole, TicketStatus, UserRole
from app.models.faculty import Faculty
from app.models.inventory_item import InventoryItem
from app.models.technician_faculty_assignment import TechnicianFacultyAssignment
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
from app.services.inventory_excel import generate_inventory_xlsx, parse_inventory_rows

router = APIRouter(prefix="/inventory", tags=["inventory"])

TECHNICIAN_ROLES = (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP)


def _check_access(current_user: User, faculty_id: int, action: str = "edit") -> None:
    if current_user.role == UserRole.SUPER_ADMIN:
        return
    if current_user.role == UserRole.ADMIN and has_permission(current_user, "inventory", action):
        return
    if current_user.role in TECHNICIAN_ROLES and faculty_id in technician_faculty_ids(current_user):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")


async def _lookup_main_technician_id(db: AsyncSession, faculty_id: int) -> int | None:
    result = await db.execute(
        select(TechnicianFacultyAssignment.user_id).where(
            TechnicianFacultyAssignment.faculty_id == faculty_id,
            TechnicianFacultyAssignment.role == TechnicianFacultyRole.TECHNICIAN_MAIN,
        )
    )
    return result.scalar_one_or_none()


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
        sub_unit=item.sub_unit,
        room=item.room,
        inventory_number=item.inventory_number,
        uzasbo=item.uzasbo,
        inventory_type=item.inventory_type,
        model=item.model,
        status=item.status,
        internet_connection=item.internet_connection,
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


async def _fetch_inventory(
    db: AsyncSession, current_user: User, faculty_id: int | None
) -> list[InventoryItemOut]:
    technician_alias = aliased(User)
    query = (
        select(InventoryItem, Faculty.name, technician_alias.full_name)
        .join(Faculty, InventoryItem.faculty_id == Faculty.id)
        .outerjoin(technician_alias, InventoryItem.assigned_technician_id == technician_alias.id)
    )

    if current_user.role == UserRole.SUPER_ADMIN or (
        current_user.role == UserRole.ADMIN and has_permission(current_user, "inventory", "view")
    ):
        if faculty_id is not None:
            query = query.where(InventoryItem.faculty_id == faculty_id)
    elif current_user.role in TECHNICIAN_ROLES:
        allowed = technician_faculty_ids(current_user)
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

    item_ids = [item.id for item, _, _ in rows]
    repair_rows = (
        await db.execute(
            select(Ticket.inventory_item_id, func.count(Ticket.id), func.max(Ticket.closed_at))
            .where(Ticket.inventory_item_id.in_(item_ids), Ticket.status == TicketStatus.CLOSED)
            .group_by(Ticket.inventory_item_id)
        )
    ).all()
    repair_map = {r[0]: (r[1], r[2]) for r in repair_rows}

    return [
        _to_out(item, faculty_name, technician_name, *repair_map.get(item.id, (0, None)))
        for item, faculty_name, technician_name in rows
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
    content = generate_inventory_xlsx(items)
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
    faculty_by_name = {f.name.strip().lower(): f for f in faculties}

    main_tech_rows = (
        await db.execute(
            select(TechnicianFacultyAssignment.faculty_id, TechnicianFacultyAssignment.user_id).where(
                TechnicianFacultyAssignment.role == TechnicianFacultyRole.TECHNICIAN_MAIN
            )
        )
    ).all()
    main_technician_by_faculty = {faculty_id: user_id for faculty_id, user_id in main_tech_rows}

    created = 0
    skipped: list[InventoryImportSkip] = []
    for row in rows:
        faculty = faculty_by_name.get(row.faculty_name.strip().lower())
        if faculty is None:
            skipped.append(
                InventoryImportSkip(
                    row=row.row_number, reason=f"Fakultet/bo'lim topilmadi: '{row.faculty_name}'"
                )
            )
            continue
        db.add(
            InventoryItem(
                faculty_id=faculty.id,
                sub_unit=row.sub_unit,
                room=row.room,
                inventory_number=row.inventory_number,
                uzasbo=row.uzasbo,
                inventory_type=row.inventory_type,
                model=row.model,
                status=row.status or "ishchi",
                internet_connection=row.internet_connection,
                responsible_person=row.responsible_person,
                assigned_technician_id=main_technician_by_faculty.get(faculty.id),
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
    _check_access(current_user, item.faculty_id, "view")

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
    _check_access(current_user, payload.faculty_id, "create")
    faculty = await db.get(Faculty, payload.faculty_id)
    if faculty is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fakultet/bo'lim topilmadi")

    data = payload.model_dump()
    if data.get("assigned_technician_id") is None:
        data["assigned_technician_id"] = await _lookup_main_technician_id(db, payload.faculty_id)

    item = InventoryItem(**data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return await _serialize_one(db, item, faculty.name)


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
    _check_access(current_user, item.faculty_id)

    data = payload.model_dump(exclude_unset=True)
    target_faculty_id = data.get("faculty_id", item.faculty_id)
    if target_faculty_id != item.faculty_id:
        _check_access(current_user, target_faculty_id)
        target_faculty = await db.get(Faculty, target_faculty_id)
        if target_faculty is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fakultet/bo'lim topilmadi")

    for field, value in data.items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)

    faculty = await db.get(Faculty, item.faculty_id)
    return await _serialize_one(db, item, faculty.name)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await db.get(InventoryItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventar topilmadi")
    _check_access(current_user, item.faculty_id, "delete")
    await db.delete(item)
    await db.commit()
