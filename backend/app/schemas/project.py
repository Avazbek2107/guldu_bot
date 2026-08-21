from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

PROJECT_STATUS_OPTIONS: list[str] = ["Rejalashtirilgan", "Jarayonda", "Yakunlangan", "To'xtatilgan"]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: str = Field(default="Rejalashtirilgan", max_length=64)
    responsible_person: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = Field(default=None, max_length=64)
    responsible_person: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: str
    responsible_person: str | None
    created_at: datetime
    updated_at: datetime
