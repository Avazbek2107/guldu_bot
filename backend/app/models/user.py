from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)

    faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculties.id"), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
    )

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    permissions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    faculty: Mapped["Faculty"] = relationship(back_populates="users")
    faculty_assignments: Mapped[list["TechnicianFacultyAssignment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    inventory_type_assignments: Mapped[list["TechnicianInventoryTypeAssignment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    tickets_created: Mapped[list["Ticket"]] = relationship(
        back_populates="created_by", foreign_keys="Ticket.created_by_user_id"
    )
    tickets_assigned: Mapped[list["Ticket"]] = relationship(
        back_populates="assigned_technician", foreign_keys="Ticket.assigned_technician_id"
    )
