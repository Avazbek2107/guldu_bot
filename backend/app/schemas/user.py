from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=5, max_length=32)
    role: UserRole
    faculty_id: int | None = None
    telegram_id: int | None = None


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=5, max_length=32)
    faculty_id: int | None = None
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
    telegram_id: int | None
    is_blocked: bool
    is_suspicious: bool
