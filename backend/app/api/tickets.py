from datetime import date, datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import TicketCategory, TicketPriority, TicketStatus, UserRole
from app.models.faculty import Faculty
from app.models.ticket import Ticket, TicketReassignment
from app.models.user import User
from app.schemas.ticket import TicketCloseRequest, TicketOut, TicketReassignRequest
from app.services.excel_generator import generate_tickets_xlsx
from app.services.pdf_generator import generate_ticket_pdf, generate_tickets_list_pdf

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _can_access_ticket_faculty(current_user: User, faculty_id: int) -> bool:
    if current_user.role == UserRole.SUPER_ADMIN:
        return True
    return (
        current_user.role in (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP)
        and current_user.faculty_id == faculty_id
    )


def _row_to_ticket_out(row) -> TicketOut:
    ticket, faculty_name, creator_full_name, creator_phone, technician_full_name = row
    return TicketOut(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        faculty_id=ticket.faculty_id,
        faculty_name=faculty_name,
        creator_full_name=creator_full_name,
        creator_phone=creator_phone,
        category=ticket.category,
        priority=ticket.priority,
        description=ticket.description,
        status=ticket.status,
        assigned_technician_id=ticket.assigned_technician_id,
        technician_full_name=technician_full_name,
        resolution_comment=ticket.resolution_comment,
        is_suspicious=ticket.is_suspicious,
        created_at=ticket.created_at,
        accepted_at=ticket.accepted_at,
        closed_at=ticket.closed_at,
    )


@router.get("", response_model=list[TicketOut])
async def list_tickets(
    faculty_id: int | None = None,
    status_filter: TicketStatus | None = Query(None, alias="status"),
    technician_id: int | None = None,
    category: TicketCategory | None = None,
    priority: TicketPriority | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    creator_alias = aliased(User)
    technician_alias = aliased(User)

    query = (
        select(Ticket, Faculty.name, creator_alias.full_name, creator_alias.phone, technician_alias.full_name)
        .join(Faculty, Ticket.faculty_id == Faculty.id)
        .join(creator_alias, Ticket.created_by_user_id == creator_alias.id)
        .outerjoin(technician_alias, Ticket.assigned_technician_id == technician_alias.id)
    )

    if current_user.role == UserRole.SUPER_ADMIN:
        if faculty_id is not None:
            query = query.where(Ticket.faculty_id == faculty_id)
    elif current_user.role in (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP):
        query = query.where(Ticket.faculty_id == current_user.faculty_id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")

    if status_filter is not None:
        query = query.where(Ticket.status == status_filter)
    if technician_id is not None:
        query = query.where(Ticket.assigned_technician_id == technician_id)
    if category is not None:
        query = query.where(Ticket.category == category)
    if priority is not None:
        query = query.where(Ticket.priority == priority)
    if date_from is not None:
        query = query.where(Ticket.created_at >= date_from)
    if date_to is not None:
        query = query.where(Ticket.created_at < date_to)

    query = query.order_by(Ticket.created_at.desc())
    result = await db.execute(query)
    return [_row_to_ticket_out(row) for row in result.all()]


@router.get("/export")
async def export_tickets(
    format: Literal["xlsx", "pdf"],
    faculty_id: int | None = None,
    status_filter: TicketStatus | None = Query(None, alias="status"),
    technician_id: int | None = None,
    category: TicketCategory | None = None,
    priority: TicketPriority | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tickets = await list_tickets(
        faculty_id=faculty_id,
        status_filter=status_filter,
        technician_id=technician_id,
        category=category,
        priority=priority,
        date_from=date_from,
        date_to=date_to,
        db=db,
        current_user=current_user,
    )

    if format == "xlsx":
        content = generate_tickets_xlsx(tickets)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "arizalar.xlsx"
    else:
        content = generate_tickets_list_pdf(tickets)
        media_type = "application/pdf"
        filename = "arizalar.pdf"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    creator_alias = aliased(User)
    technician_alias = aliased(User)

    query = (
        select(Ticket, Faculty.name, creator_alias.full_name, creator_alias.phone, technician_alias.full_name)
        .join(Faculty, Ticket.faculty_id == Faculty.id)
        .join(creator_alias, Ticket.created_by_user_id == creator_alias.id)
        .outerjoin(technician_alias, Ticket.assigned_technician_id == technician_alias.id)
        .where(Ticket.id == ticket_id)
    )
    result = await db.execute(query)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ariza topilmadi")

    ticket = row[0]
    if not _can_access_ticket_faculty(current_user, ticket.faculty_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")

    return _row_to_ticket_out(row)


@router.patch("/{ticket_id}/close", response_model=TicketOut)
async def close_ticket(
    ticket_id: int,
    payload: TicketCloseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ariza topilmadi")
    if not _can_access_ticket_faculty(current_user, ticket.faculty_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")

    ticket.status = TicketStatus.CLOSED
    ticket.closed_at = datetime.now(timezone.utc)
    ticket.resolution_comment = payload.resolution_comment
    await db.commit()

    return await get_ticket(ticket_id, db, current_user)


@router.patch("/{ticket_id}/reassign", response_model=TicketOut)
async def reassign_ticket(
    ticket_id: int,
    payload: TicketReassignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ariza topilmadi")
    if not _can_access_ticket_faculty(current_user, ticket.faculty_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")

    technician = await db.get(User, payload.technician_id)
    if (
        technician is None
        or technician.role not in (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP)
        or technician.faculty_id != ticket.faculty_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Texnik xodim shu fakultetga tegishli emas"
        )

    db.add(
        TicketReassignment(
            ticket_id=ticket.id,
            from_technician_id=ticket.assigned_technician_id,
            to_technician_id=technician.id,
            reason=f"{current_user.full_name} tomonidan admin panel orqali qayta yo'naltirildi",
        )
    )
    ticket.assigned_technician_id = technician.id
    await db.commit()

    return await get_ticket(ticket_id, db, current_user)


@router.get("/{ticket_id}/pdf")
async def get_ticket_pdf(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ariza topilmadi")

    if not _can_access_ticket_faculty(current_user, ticket.faculty_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")

    creator = await db.get(User, ticket.created_by_user_id)
    faculty = await db.get(Faculty, ticket.faculty_id)
    technician = await db.get(User, ticket.assigned_technician_id) if ticket.assigned_technician_id else None

    pdf_bytes = generate_ticket_pdf(ticket, creator, faculty.name, technician)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={ticket.ticket_number}.pdf"},
    )
