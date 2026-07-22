from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.faculty import Faculty
from app.models.ticket import Ticket
from app.models.user import User
from app.services.pdf_generator import generate_ticket_pdf

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("/{ticket_id}/pdf")
async def get_ticket_pdf(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ariza topilmadi")

    if current_user.role != UserRole.SUPER_ADMIN and (
        current_user.role not in (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP)
        or current_user.faculty_id != ticket.faculty_id
    ):
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
