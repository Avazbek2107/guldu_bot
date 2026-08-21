from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

PAYMENT_CATEGORY_OPTIONS: list[str] = ["Zoom", "SSL", "Internet", "Domen", "Boshqa"]

DUE_SOON_THRESHOLD_DAYS = 14


def compute_payment_status(due_date: date, today: date | None = None) -> tuple[str, int]:
    """Status is derived from the due date rather than stored, so it's never
    stale — an admin who forgets to update a record still sees an accurate
    "muddati o'tgan" warning the day after it lapses."""
    today = today or date.today()
    days_left = (due_date - today).days
    if days_left < 0:
        return "Muddati o'tgan", days_left
    if days_left <= DUE_SOON_THRESHOLD_DAYS:
        return "Tez orada", days_left
    return "Faol", days_left


class ServicePaymentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = Field(max_length=64)
    amount: float | None = None
    due_date: date
    responsible_person: str | None = None
    notes: str | None = None


class ServicePaymentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=64)
    amount: float | None = None
    due_date: date | None = None
    responsible_person: str | None = None
    notes: str | None = None


class ServicePaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    amount: float | None
    due_date: date
    responsible_person: str | None
    notes: str | None
    status: str
    days_left: int
    created_at: datetime
    updated_at: datetime
