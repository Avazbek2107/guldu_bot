from datetime import datetime

from pydantic import BaseModel


class ReporterStat(BaseModel):
    user_id: int
    full_name: str
    phone: str
    faculty_id: int | None
    faculty_name: str | None
    total_tickets: int
    open_tickets: int
    suspicious_tickets: int
    last_ticket_at: datetime | None


class FacultyStat(BaseModel):
    faculty_id: int
    faculty_name: str
    total: int
    open: int
    in_progress: int
    closed: int


class TechnicianStat(BaseModel):
    technician_id: int
    full_name: str
    accepted: int
    closed: int
    open_remaining: int
    avg_close_hours: float | None
    efficiency_percent: float | None


class CategoryStat(BaseModel):
    category: str
    count: int


class DailyCount(BaseModel):
    date: str
    count: int


class InventoryStatusStat(BaseModel):
    status: str
    count: int


class InventoryFacultyStat(BaseModel):
    faculty_id: int
    faculty_name: str
    total: int
    working: int
    broken: int
    in_repair: int
    decommissioned: int


class DashboardStats(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    closed_tickets: int
    faculty_stats: list[FacultyStat]
    technician_stats: list[TechnicianStat]
    reporter_stats: list[ReporterStat]
    category_stats: list[CategoryStat]
    suspicious_user_count: int
    blocked_user_count: int
    daily_trend: list[DailyCount]
    total_inventory_items: int
    inventory_status_stats: list[InventoryStatusStat]
    inventory_faculty_stats: list[InventoryFacultyStat]
