from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

INVENTORY_TYPE_OPTIONS: list[str] = [
    "Monoblok",
    "Kompyuter",
    "Noutbook",
    "Server",
    "Interaktiv panel",
    "Wi-Fi",
    "Printer",
    "3in1 printer",
    "Skaner",
    "Proyektor",
    "E-minbar",
    "Televizor",
    "Kamera",
    "NVR",
    "Switch",
    "PoE Switch",
    "HUB",
]

INVENTORY_STATUS_OPTIONS: list[str] = ["Ishchi", "Ta'mir talab", "Yaroqsiz"]

INVENTORY_INTERNET_OPTIONS: list[str] = [
    "Internetga ulangan (kabeli bor)",
    "Internetga ulanmagan (kabeli yo'q)",
    "Wifi",
]

MAC_ADDRESS_INVENTORY_TYPES: set[str] = {"Monoblok", "Kompyuter", "Noutbook", "Interaktiv panel"}


class InventoryItemCreate(BaseModel):
    faculty_id: int
    room: str | None = None
    inventory_number: str | None = None
    uzasbo: str | None = None
    inventory_type: str | None = None
    model: str | None = None
    status: str = Field(default="Ishchi", max_length=64)
    internet_connection: str | None = None
    mac_address: str | None = None
    responsible_person: str | None = None
    assigned_technician_id: int | None = None


class InventoryItemUpdate(BaseModel):
    faculty_id: int | None = None
    room: str | None = None
    inventory_number: str | None = None
    uzasbo: str | None = None
    inventory_type: str | None = None
    model: str | None = None
    status: str | None = Field(default=None, max_length=64)
    internet_connection: str | None = None
    mac_address: str | None = None
    responsible_person: str | None = None
    assigned_technician_id: int | None = None


class InventoryItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    faculty_id: int
    faculty_name: str
    room: str | None
    inventory_number: str | None
    uzasbo: str | None
    inventory_type: str | None
    model: str | None
    status: str
    internet_connection: str | None
    mac_address: str | None
    responsible_person: str | None
    assigned_technician_id: int | None
    assigned_technician_name: str | None
    repair_count: int
    last_repaired_at: datetime | None
    created_at: datetime


class RepairHistoryItem(BaseModel):
    ticket_id: int
    ticket_number: str
    closed_at: datetime | None
    resolution_comment: str | None
    technician_full_name: str | None
    is_suspicious: bool


class InventoryImportSkip(BaseModel):
    row: int
    reason: str


class InventoryImportResult(BaseModel):
    created: int
    skipped: list[InventoryImportSkip]
