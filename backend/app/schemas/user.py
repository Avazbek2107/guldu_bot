from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    phone: str
    role: UserRole
    faculty_id: int | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    faculty_id: int | None = None
    password: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str | None
    full_name: str
    phone: str
    role: UserRole
    faculty_id: int | None
    is_blocked: bool
    is_suspicious: bool
