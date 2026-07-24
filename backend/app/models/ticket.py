from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import AttachmentType, TicketCategory, TicketPriority, TicketStatus


def _enum_values(enum_cls):
    return [e.value for e in enum_cls]


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"
    __table_args__ = (Index("ix_tickets_created_at", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"), nullable=False, index=True)

    category: Mapped[TicketCategory] = mapped_column(
        SAEnum(TicketCategory, name="ticket_category", values_callable=_enum_values), nullable=False
    )
    priority: Mapped[TicketPriority] = mapped_column(
        SAEnum(TicketPriority, name="ticket_priority", values_callable=_enum_values), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[TicketStatus] = mapped_column(
        SAEnum(TicketStatus, name="ticket_status", values_callable=_enum_values),
        default=TicketStatus.OPEN,
        nullable=False,
        index=True,
    )
    assigned_technician_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    inventory_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("inventory_items.id", ondelete="SET NULL"), nullable=True, index=True
    )

    resolution_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    suspicious_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped["User"] = relationship(back_populates="tickets_created", foreign_keys=[created_by_user_id])
    assigned_technician: Mapped["User | None"] = relationship(
        back_populates="tickets_assigned", foreign_keys=[assigned_technician_id]
    )
    faculty: Mapped["Faculty"] = relationship(back_populates="tickets")
    inventory_item: Mapped["InventoryItem | None"] = relationship(back_populates="repairs")

    attachments: Mapped[list["TicketAttachment"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")
    reassignments: Mapped[list["TicketReassignment"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[AttachmentType] = mapped_column(
        SAEnum(AttachmentType, name="attachment_type", values_callable=_enum_values), nullable=False
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ticket: Mapped["Ticket"] = relationship(back_populates="attachments")


class TicketReassignment(Base):
    __tablename__ = "ticket_reassignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    from_technician_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    to_technician_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ticket: Mapped["Ticket"] = relationship(back_populates="reassignments")
