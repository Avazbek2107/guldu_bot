from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        Index(
            "ix_one_main_technician_per_faculty",
            "faculty_id",
            unique=True,
            postgresql_where="role = 'technician_main'",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_id: Mapped[int | None] = mapped_column(unique=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)

    faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculties.id"), nullable=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"), nullable=False)

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    faculty: Mapped["Faculty"] = relationship(back_populates="users")
    tickets_created: Mapped[list["Ticket"]] = relationship(
        back_populates="created_by", foreign_keys="Ticket.created_by_user_id"
    )
    tickets_assigned: Mapped[list["Ticket"]] = relationship(
        back_populates="assigned_technician", foreign_keys="Ticket.assigned_technician_id"
    )
