from pydantic import BaseModel


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
    faculty_id: int | None
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


class DashboardStats(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    closed_tickets: int
    faculty_stats: list[FacultyStat]
    technician_stats: list[TechnicianStat]
    category_stats: list[CategoryStat]
    average_rating: float | None
    sla_breach_count: int
    sla_open_breach_count: int
    suspicious_user_count: int
    blocked_user_count: int
    daily_trend: list[DailyCount]
