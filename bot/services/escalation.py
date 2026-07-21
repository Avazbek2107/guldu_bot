import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.enums import TicketStatus
from app.models.ticket import Ticket

from bot.services.tickets import notify_backup_technicians, notify_sla_breach

logger = logging.getLogger(__name__)


async def check_backup_escalation(bot, db: AsyncSession, backup_after_minutes: int) -> None:
    threshold = datetime.now(timezone.utc) - timedelta(minutes=backup_after_minutes)
    result = await db.execute(
        select(Ticket).where(
            Ticket.status == TicketStatus.OPEN,
            Ticket.escalated_at.is_(None),
            Ticket.created_at <= threshold,
        )
    )
    for ticket in result.scalars().all():
        await notify_backup_technicians(bot, db, ticket)
        ticket.escalated_at = datetime.now(timezone.utc)
        await db.commit()


async def check_sla_breach(bot, db: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Ticket).where(
            Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS]),
            Ticket.sla_breach_notified_at.is_(None),
            Ticket.sla_deadline.is_not(None),
            Ticket.sla_deadline < now,
        )
    )
    for ticket in result.scalars().all():
        await notify_sla_breach(bot, db, ticket)
        ticket.sla_breach_notified_at = now
        await db.commit()


async def run_escalation_loop(
    bot,
    session_factory: async_sessionmaker[AsyncSession],
    interval_seconds: int,
    backup_after_minutes: int,
) -> None:
    while True:
        try:
            async with session_factory() as db:
                await check_backup_escalation(bot, db, backup_after_minutes)
                await check_sla_breach(bot, db)
        except Exception:
            logger.exception("Eskalatsiya tsiklida xatolik")
        await asyncio.sleep(interval_seconds)
