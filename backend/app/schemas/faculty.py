from pydantic import BaseModel, ConfigDict

from app.models.enums import OrgUnitType


class FacultyCreate(BaseModel):
    name: str
    unit_type: OrgUnitType = OrgUnitType.FACULTY


class FacultyUpdate(BaseModel):
    name: str


class FacultyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    unit_type: OrgUnitType
