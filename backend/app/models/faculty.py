from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import OrgUnitType


class Faculty(Base):
    __tablename__ = "faculties"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    unit_type: Mapped[OrgUnitType] = mapped_column(
        SAEnum(OrgUnitType, name="org_unit_type", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
        default=OrgUnitType.FACULTY,
        server_default=OrgUnitType.FACULTY.value,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="faculty")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="faculty")
    technician_assignments: Mapped[list["TechnicianFacultyAssignment"]] = relationship(back_populates="faculty")
    inventory_items: Mapped[list["InventoryItem"]] = relationship(back_populates="faculty")
