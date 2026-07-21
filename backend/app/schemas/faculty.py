from typing import Literal

from pydantic import BaseModel, ConfigDict


class FacultyCreate(BaseModel):
    name: str


class FacultyUpdate(BaseModel):
    name: str


class FacultyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class AssignTechnicianRequest(BaseModel):
    user_id: int
    role: Literal["technician_main", "technician_backup"]
