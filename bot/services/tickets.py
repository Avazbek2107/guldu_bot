from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AttachmentType, TechnicianFacultyRole, TicketCategory, TicketPriority, TicketStatus, UserRole
from app.models.technician_faculty_assignment import TechnicianFacultyAssignment
from app.models.ticket import Ticket, TicketAttachment, TicketReassignment
from app.models.user import User

from bot.keyboards import accept_ticket_keyboard, ticket_actions_keyboard


async def create_ticket(
    db: AsyncSession,
    *,
    created_by: User,
    description: str,
    category: TicketCategory,
    priority: TicketPriority,
    attachments: list[tuple[str, AttachmentType]] | None = None,
) -> Ticket:
    now = datetime.now(timezone.utc)

    ticket = Ticket(
        ticket_number="pending",
        created_by_user_id=created_by.id,
        faculty_id=created_by.faculty_id,
        category=category,
        priority=priority,
        description=description,
    )
    db.add(ticket)
    await db.flush()
    ticket.ticket_number = f"T-{now.year}-{ticket.id:06d}"

    for file_path, file_type in attachments or []:
        db.add(TicketAttachment(ticket_id=ticket.id, file_path=file_path, file_type=file_type))

    await db.commit()
    await db.refresh(ticket)
    return ticket


async def count_open_tickets_for_faculty(db: AsyncSession, faculty_id: int) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Ticket)
        .where(
            Ticket.faculty_id == faculty_id,
            Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS]),
        )
    )
    return result.scalar_one()


async def get_faculty_technician_main(db: AsyncSession, faculty_id: int) -> User | None:
    result = await db.execute(
        select(User)
        .join(TechnicianFacultyAssignment, TechnicianFacultyAssignment.user_id == User.id)
        .where(
            TechnicianFacultyAssignment.faculty_id == faculty_id,
            TechnicianFacultyAssignment.role == TechnicianFacultyRole.TECHNICIAN_MAIN,
        )
    )
    return result.scalar_one_or_none()


async def get_faculty_technicians_backup(db: AsyncSession, faculty_id: int) -> list[User]:
    result = await db.execute(
        select(User)
        .join(TechnicianFacultyAssignment, TechnicianFacultyAssignment.user_id == User.id)
        .where(
            TechnicianFacultyAssignment.faculty_id == faculty_id,
            TechnicianFacultyAssignment.role == TechnicianFacultyRole.TECHNICIAN_BACKUP,
        )
    )
    return list(result.scalars().all())


async def get_faculty_technicians(
    db: AsyncSession, faculty_id: int, exclude_user_id: int | None = None
) -> list[User]:
    query = select(User).join(TechnicianFacultyAssignment, TechnicianFacultyAssignment.user_id == User.id).where(
        TechnicianFacultyAssignment.faculty_id == faculty_id,
        User.role.in_([UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP]),
    )
    if exclude_user_id is not None:
        query = query.where(User.id != exclude_user_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def is_technician_assigned(db: AsyncSession, user_id: int, faculty_id: int) -> bool:
    result = await db.execute(
        select(TechnicianFacultyAssignment.id).where(
            TechnicianFacultyAssignment.user_id == user_id,
            TechnicianFacultyAssignment.faculty_id == faculty_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def can_close_ticket(db: AsyncSession, ticket: Ticket, user: User) -> bool:
    if user.id == ticket.created_by_user_id:
        return True
    if user.role in (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP) and await is_technician_assigned(
        db, user.id, ticket.faculty_id
    ):
        return True
    return user.role == UserRole.SUPER_ADMIN


async def accept_ticket(db: AsyncSession, ticket: Ticket, technician: User) -> bool:
    """Atomically claim an open ticket. Returns False if another technician already accepted it."""
    result = await db.execute(
        update(Ticket)
        .where(Ticket.id == ticket.id, Ticket.status == TicketStatus.OPEN)
        .values(
            status=TicketStatus.IN_PROGRESS,
            accepted_at=datetime.now(timezone.utc),
            assigned_technician_id=technician.id,
        )
    )
    await db.commit()
    if result.rowcount == 0:
        return False
    await db.refresh(ticket)
    return True


async def close_ticket(
    db: AsyncSession,
    ticket: Ticket,
    resolution_comment: str | None,
    is_suspicious: bool,
    suspicious_comment: str | None,
    inventory_item_id: int,
    closing_attachment: tuple[str, AttachmentType] | None = None,
) -> bool:
    """Atomically close a not-yet-closed ticket. Returns False (no-op) if it was
    already closed — e.g. a double-tapped button or two technicians racing to
    close the same ticket — so the caller can avoid a duplicate attachment row
    and a misleading "success" message."""
    result = await db.execute(
        update(Ticket)
        .where(Ticket.id == ticket.id, Ticket.status != TicketStatus.CLOSED)
        .values(
            status=TicketStatus.CLOSED,
            closed_at=datetime.now(timezone.utc),
            resolution_comment=resolution_comment,
            is_suspicious=is_suspicious,
            suspicious_comment=suspicious_comment,
            inventory_item_id=inventory_item_id,
        )
    )
    if result.rowcount == 0:
        await db.rollback()
        return False
    if is_suspicious:
        creator = await db.get(User, ticket.created_by_user_id)
        creator.is_suspicious = True
    if closing_attachment is not None:
        file_path, file_type = closing_attachment
        db.add(TicketAttachment(ticket_id=ticket.id, file_path=file_path, file_type=file_type))
    await db.commit()
    await db.refresh(ticket)
    return True


async def reassign_ticket(
    db: AsyncSession, ticket: Ticket, from_technician: User, to_technician: User, reason: str
) -> bool:
    if ticket.status == TicketStatus.CLOSED:
        return False
    db.add(
        TicketReassignment(
            ticket_id=ticket.id,
            from_technician_id=from_technician.id,
            to_technician_id=to_technician.id,
            reason=reason,
        )
    )
    ticket.assigned_technician_id = to_technician.id
    await db.commit()
    return True


CATEGORY_LABELS_UZ = {
    "computer": "Kompyuter",
    "network": "Tarmoq/internet",
    "projector": "Proyektor",
    "power": "Elektr ta'minoti",
    "printer": "Printer",
    "software": "Dasturiy ta'minot",
    "other": "Boshqa",
}
PRIORITY_LABELS_UZ = {"urgent": "Shoshilinch", "normal": "Oddiy"}


def format_ticket_message(ticket: Ticket, creator: User, open_count: int) -> str:
    return (
        f"🆕 Ariza #{ticket.ticket_number}\n\n"
        f"👤 FISH: {creator.full_name}\n"
        f"📞 Telefon: {creator.phone}\n"
        f"📝 Tavsif: {ticket.description}\n"
        f"🏷 Toifa: {CATEGORY_LABELS_UZ.get(ticket.category.value, ticket.category.value)}\n"
        f"⚡ Muhimlik: {PRIORITY_LABELS_UZ.get(ticket.priority.value, ticket.priority.value)}\n"
        f"🕐 Sana: {ticket.created_at.strftime('%Y-%m-%d %H:%M') if ticket.created_at else '-'}\n"
        f"📊 Joriy ochiq arizalar: {open_count}"
    )


async def notify_new_ticket(bot, db: AsyncSession, ticket: Ticket) -> None:
    technician = await get_faculty_technician_main(db, ticket.faculty_id)
    if technician is None or technician.telegram_id is None:
        return
    creator = await db.get(User, ticket.created_by_user_id)
    open_count = await count_open_tickets_for_faculty(db, ticket.faculty_id)
    text = format_ticket_message(ticket, creator, open_count)
    await bot.send_message(technician.telegram_id, text, reply_markup=accept_ticket_keyboard(ticket.id))


async def notify_backup_technicians(bot, db: AsyncSession, ticket: Ticket) -> None:
    creator = await db.get(User, ticket.created_by_user_id)
    open_count = await count_open_tickets_for_faculty(db, ticket.faculty_id)
    text = "⏰ ESKALATSIYA (30 daqiqa javobsiz)\n\n" + format_ticket_message(ticket, creator, open_count)
    for tech in await get_faculty_technicians_backup(db, ticket.faculty_id):
        if tech.telegram_id:
            await bot.send_message(tech.telegram_id, text, reply_markup=accept_ticket_keyboard(ticket.id))


async def notify_reassignment(bot, db: AsyncSession, ticket: Ticket, to_technician: User, reason: str) -> None:
    if not to_technician.telegram_id:
        return
    creator = await db.get(User, ticket.created_by_user_id)
    open_count = await count_open_tickets_for_faculty(db, ticket.faculty_id)
    text = (
        f"↪️ Sizga ariza qayta yo'naltirildi\nSabab: {reason}\n\n"
        + format_ticket_message(ticket, creator, open_count)
    )
    await bot.send_message(to_technician.telegram_id, text, reply_markup=ticket_actions_keyboard(ticket.id))


async def notify_ticket_accepted(bot, ticket: Ticket, creator: User) -> None:
    if creator.telegram_id:
        await bot.send_message(
            creator.telegram_id,
            f"✅ Arizangiz (#{ticket.ticket_number}) texnik xodim tomonidan qabul qilindi va jarayonda.",
        )


async def notify_ticket_closed(bot, ticket: Ticket, creator: User) -> None:
    if creator.telegram_id:
        await bot.send_message(
            creator.telegram_id,
            f"✅ Arizangiz (#{ticket.ticket_number}) yopildi.",
        )
