from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.permissions import PERMISSION_ACTIONS, PERMISSION_RESOURCES
from app.models.enums import TechnicianFacultyRole, UserRole
from app.schemas.inventory import INVENTORY_TYPE_OPTIONS

if TYPE_CHECKING:
    from app.models.user import User

TECHNICIAN_ROLES = (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP)


def validate_permissions(role: UserRole, permissions: dict[str, list[str]] | None) -> dict[str, list[str]] | None:
    if role != UserRole.ADMIN:
        if permissions:
            raise ValueError("Faqat Admin roli uchun ruxsatlar belgilanadi")
        return None

    if not permissions:
        return {}

    cleaned: dict[str, list[str]] = {}
    for resource, actions in permissions.items():
        if resource not in PERMISSION_RESOURCES:
            raise ValueError(f"Noto'g'ri bo'lim: '{resource}'")
        invalid = [a for a in actions if a not in PERMISSION_ACTIONS]
        if invalid:
            raise ValueError(f"Noto'g'ri amal: '{', '.join(invalid)}'")
        cleaned[resource] = list(dict.fromkeys(actions))
    return cleaned


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


def validate_inventory_type_assignments(role: UserRole, inventory_types: list[str]) -> list[str]:
    if role not in TECHNICIAN_ROLES:
        if inventory_types:
            raise ValueError("Faqat texnik xodim uchun inventar toifasi biriktirish mumkin")
        return inventory_types

    invalid = [t for t in inventory_types if t not in INVENTORY_TYPE_OPTIONS]
    if invalid:
        raise ValueError(f"Noto'g'ri inventar toifasi: '{', '.join(invalid)}'")
    if len(inventory_types) != len(set(inventory_types)):
        raise ValueError("Bitta toifa faqat bir marta tanlanishi mumkin")
    return inventory_types


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=5, max_length=32)
    role: UserRole
    faculty_assignments: list[FacultyAssignmentIn] = []
    inventory_type_assignments: list[str] = []
    permissions: dict[str, list[str]] | None = None
    telegram_id: int | None = None

    @model_validator(mode="after")
    def _check_assignments(self) -> "UserCreate":
        validate_faculty_assignments(self.role, self.faculty_assignments)
        validate_inventory_type_assignments(self.role, self.inventory_type_assignments)
        self.permissions = validate_permissions(self.role, self.permissions)
        return self


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=5, max_length=32)
    faculty_id: int | None = None
    faculty_assignments: list[FacultyAssignmentIn] | None = None
    inventory_type_assignments: list[str] | None = None
    permissions: dict[str, list[str]] | None = None
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
    inventory_type_assignments: list[str] = []
    permissions: dict[str, list[str]] | None = None
    avatar_url: str | None = None
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
        inventory_type_assignments=[a.inventory_type for a in user.inventory_type_assignments],
        permissions=user.permissions,
        avatar_url=f"/storage/{user.avatar_path}" if user.avatar_path else None,
        telegram_id=user.telegram_id,
        is_blocked=user.is_blocked,
        is_suspicious=user.is_suspicious,
    )
