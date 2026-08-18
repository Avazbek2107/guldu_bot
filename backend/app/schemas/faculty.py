from pydantic import BaseModel, ConfigDict

from app.models.enums import OrgUnitType


class FacultyCreate(BaseModel):
    name: str
    unit_type: OrgUnitType = OrgUnitType.FACULTY
    parent_id: int | None = None


class FacultyUpdate(BaseModel):
    name: str


class FacultyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    unit_type: OrgUnitType
    parent_id: int | None = None


class FacultyImportSkip(BaseModel):
    row: int
    reason: str


class FacultyImportResult(BaseModel):
    created: int
    skipped: list[FacultyImportSkip]
