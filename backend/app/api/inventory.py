from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.deps import get_current_user, require_roles, technician_faculty_ids
from app.core.database import get_db
from app.models.enums import TicketStatus, UserRole
from app.models.faculty import Faculty
from app.models.inventory_item import InventoryItem
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


def _check_access(current_user: User, faculty_id: int) -> None:
    if current_user.role == UserRole.SUPER_ADMIN:
        return
    if current_user.role in TECHNICIAN_ROLES and faculty_id in technician_faculty_ids(current_user):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")


def _to_out(item: InventoryItem, faculty_name: str, repair_count: int, last_repaired_at) -> InventoryItemOut:
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
    return _to_out(item, faculty_name, stats[0] or 0, stats[1])


async def _fetch_inventory(
    db: AsyncSession, current_user: User, faculty_id: int | None
) -> list[InventoryItemOut]:
    query = select(InventoryItem, Faculty.name).join(Faculty, InventoryItem.faculty_id == Faculty.id)

    if current_user.role == UserRole.SUPER_ADMIN:
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

    item_ids = [item.id for item, _ in rows]
    repair_rows = (
        await db.execute(
            select(Ticket.inventory_item_id, func.count(Ticket.id), func.max(Ticket.closed_at))
            .where(Ticket.inventory_item_id.in_(item_ids), Ticket.status == TicketStatus.CLOSED)
            .group_by(Ticket.inventory_item_id)
        )
    ).all()
    repair_map = {r[0]: (r[1], r[2]) for r in repair_rows}

    return [
        _to_out(item, faculty_name, *repair_map.get(item.id, (0, None)))
        for item, faculty_name in rows
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


@router.post(
    "/import",
    response_model=InventoryImportResult,
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def import_inventory(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    content = await file.read()
    try:
        rows = parse_inventory_rows(content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Fayl formatini o'qib bo'lmadi"
        ) from exc

    faculties = (await db.execute(select(Faculty))).scalars().all()
    faculty_by_name = {f.name.strip().lower(): f for f in faculties}

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
    _check_access(current_user, item.faculty_id)

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
    _check_access(current_user, payload.faculty_id)
    faculty = await db.get(Faculty, payload.faculty_id)
    if faculty is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fakultet/bo'lim topilmadi")

    item = InventoryItem(**payload.model_dump())
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
    _check_access(current_user, item.faculty_id)
    await db.delete(item)
    await db.commit()
