from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
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
    # Set only for a kafedra nested under a faculty (unit_type=DEPARTMENT with a
    # parent). Top-level faculties and standalone administrative bo'lims (e.g.
    # Devonxona) leave this null. Cascades so deleting a faculty removes its
    # kafedras, but a kafedra that still has users/tickets/inventory pointing at
    # it cannot itself be deleted (those FKs have no cascade).
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("faculties.id", ondelete="CASCADE"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parent: Mapped["Faculty | None"] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["Faculty"]] = relationship(back_populates="parent", cascade="all, delete-orphan")

    users: Mapped[list["User"]] = relationship(back_populates="faculty")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="faculty")
    technician_assignments: Mapped[list["TechnicianFacultyAssignment"]] = relationship(back_populates="faculty")
    inventory_items: Mapped[list["InventoryItem"]] = relationship(back_populates="faculty")
