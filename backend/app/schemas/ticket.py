from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import TicketCategory, TicketPriority, TicketStatus


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_number: str
    faculty_id: int
    faculty_name: str
    creator_full_name: str
    creator_phone: str
    category: TicketCategory
    priority: TicketPriority
    description: str
    status: TicketStatus
    assigned_technician_id: int | None
    technician_full_name: str | None
    resolution_comment: str | None
    is_suspicious: bool
    created_at: datetime
    accepted_at: datetime | None
    closed_at: datetime | None


class TicketCloseRequest(BaseModel):
    resolution_comment: str | None = None


class TicketReassignRequest(BaseModel):
    technician_id: int
