from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TicketStatus
from app.models.inventory_item import InventoryItem
from app.models.ticket import Ticket


async def find_inventory_item(db: AsyncSession, faculty_id: int, inventory_number: str) -> InventoryItem | None:
    number = inventory_number.strip()
    if not number:
        return None
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.faculty_id == faculty_id,
            func.lower(InventoryItem.inventory_number) == number.lower(),
        )
    )
    return result.scalars().first()


async def list_inventory_page(
    db: AsyncSession, faculty_id: int, offset: int, limit: int
) -> tuple[list[InventoryItem], int]:
    total = (
        await db.execute(
            select(func.count()).select_from(InventoryItem).where(InventoryItem.faculty_id == faculty_id)
        )
    ).scalar_one()
    rows = (
        await db.execute(
            select(InventoryItem)
            .where(InventoryItem.faculty_id == faculty_id)
            .order_by(InventoryItem.room, InventoryItem.inventory_number)
            .offset(offset)
            .limit(limit)
        )
    ).scalars().all()
    return list(rows), total


async def count_repairs(db: AsyncSession, inventory_item_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(Ticket).where(
            Ticket.inventory_item_id == inventory_item_id, Ticket.status == TicketStatus.CLOSED
        )
    )
    return result.scalar_one()
