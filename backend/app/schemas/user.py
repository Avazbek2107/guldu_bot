from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import TechnicianFacultyRole, UserRole

if TYPE_CHECKING:
    from app.models.user import User

TECHNICIAN_ROLES = (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP)


class FacultyAssignmentIn(BaseModel):
    faculty_id: int
    role: TechnicianFacultyRole


class FacultyAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    faculty_id: int
    faculty_name: str
    role: TechnicianFacultyRole


def validate_faculty_assignments(role: UserRole, assignments: list[FacultyAssignmentIn]) -> list[FacultyAssignmentIn]:
    if role not in TECHNICIAN_ROLES:
        if assignments:
            raise ValueError("Faqat texnik xodim uchun fakultet biriktirish mumkin")
        return assignments

    if not assignments:
        raise ValueError("Texnik xodim uchun kamida bitta fakultet tanlang")

    faculty_ids = [a.faculty_id for a in assignments]
    if len(faculty_ids) != len(set(faculty_ids)):
        raise ValueError("Bitta fakultet faqat bir marta tanlanishi mumkin")

    # A technician CAN be "asosiy" (main) in several different faculties/departments
    # at once — the rule that's actually enforced is "at most one main technician
    # PER FACULTY", which is handled by the DB partial unique index + auto-demote
    # logic in app/api/users.py._apply_assignments, not here.
    return assignments


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=5, max_length=32)
    role: UserRole
    faculty_assignments: list[FacultyAssignmentIn] = []
    telegram_id: int | None = None

    @model_validator(mode="after")
    def _check_assignments(self) -> "UserCreate":
        validate_faculty_assignments(self.role, self.faculty_assignments)
        return self


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=5, max_length=32)
    faculty_id: int | None = None
    faculty_assignments: list[FacultyAssignmentIn] | None = None
    password: str | None = Field(default=None, min_length=8, max_length=100)
    telegram_id: int | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str | None
    full_name: str
    phone: str
    role: UserRole
    faculty_id: int | None
    faculty_assignments: list[FacultyAssignmentOut] = []
    telegram_id: int | None
    is_blocked: bool
    is_suspicious: bool


def serialize_user(user: "User", visible_faculty_ids: set[int] | None = None) -> UserOut:
    """Build a UserOut from an ORM User whose `faculty_assignments.faculty` relationship
    chain has been eager-loaded. `FacultyAssignmentOut.faculty_name` cannot be resolved by
    pydantic's automatic from_attributes mapping (it lives on the related Faculty, not the
    assignment row), so this must be built manually rather than via UserOut.model_validate().
    """
    assignments = user.faculty_assignments
    if visible_faculty_ids is not None:
        assignments = [a for a in assignments if a.faculty_id in visible_faculty_ids]
    return UserOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        faculty_id=user.faculty_id,
        faculty_assignments=[
            FacultyAssignmentOut(faculty_id=a.faculty_id, faculty_name=a.faculty.name, role=a.role)
            for a in assignments
        ],
        telegram_id=user.telegram_id,
        is_blocked=user.is_blocked,
        is_suspicious=user.is_suspicious,
    )
