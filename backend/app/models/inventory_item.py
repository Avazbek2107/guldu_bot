from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class InventoryItem(Base, TimestampMixin):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"), nullable=False, index=True)

    sub_unit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    room: Mapped[str | None] = mapped_column(String(64), nullable=True)
    inventory_number: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    uzasbo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    inventory_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="ishchi", nullable=False)
    internet_connection: Mapped[str | None] = mapped_column(String(128), nullable=True)
    responsible_person: Mapped[str | None] = mapped_column(String(255), nullable=True)

    faculty: Mapped["Faculty"] = relationship(back_populates="inventory_items")
    repairs: Mapped[list["Ticket"]] = relationship(back_populates="inventory_item")
