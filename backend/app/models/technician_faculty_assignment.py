from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import TechnicianFacultyRole


class TechnicianFacultyAssignment(Base):
    __tablename__ = "technician_faculty_assignments"
    __table_args__ = (
        UniqueConstraint("user_id", "faculty_id", name="uq_tech_faculty_assignment"),
        Index(
            "ix_one_main_tech_per_faculty_assignment",
            "faculty_id",
            unique=True,
            postgresql_where="role = 'technician_main'",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    faculty_id: Mapped[int] = mapped_column(
        ForeignKey("faculties.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[TechnicianFacultyRole] = mapped_column(
        SAEnum(
            TechnicianFacultyRole,
            name="technician_faculty_role",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="faculty_assignments")
    faculty: Mapped["Faculty"] = relationship(back_populates="technician_assignments")
