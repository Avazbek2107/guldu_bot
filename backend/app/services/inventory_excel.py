import io
from collections.abc import Sequence
from dataclasses import dataclass

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from app.schemas.inventory import InventoryItemOut

HEADERS = [
    "№", "FAKULTET", "FAKULTET, KAFEDRA, BO'LIM", "XONA", "INVENTAR RAQAMI",
    "INVENTAR UZASBO", "INVENTAR TOIFASI", "MODELI", "XOLATI",
    "INTERNETGA ULANGANLIGI", "MA'SUL SHAXS",
]
COLUMN_WIDTHS = [6, 26, 26, 12, 16, 18, 20, 20, 12, 24, 22]


def generate_inventory_xlsx(items: Sequence[InventoryItemOut]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Inventar"

    ws.append(HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for index, item in enumerate(items, start=1):
        ws.append(
            [
                index,
                item.faculty_name,
                item.sub_unit or "",
                item.room or "",
                item.inventory_number or "",
                item.uzasbo or "",
                item.inventory_type or "",
                item.model or "",
                item.status or "",
                item.internet_connection or "",
                item.responsible_person or "",
            ]
        )

    for col_index, width in enumerate(COLUMN_WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(col_index)].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


@dataclass
class InventoryImportRow:
    row_number: int
    faculty_name: str
    sub_unit: str | None
    room: str | None
    inventory_number: str | None
    uzasbo: str | None
    inventory_type: str | None
    model: str | None
    status: str | None
    internet_connection: str | None
    responsible_person: str | None


def _clean(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_status(value) -> str:
    cleaned = _clean(value)
    if cleaned is None:
        return "ishchi"
    return cleaned.lower()


def parse_inventory_rows(file_bytes: bytes) -> list[InventoryImportRow]:
    wb = load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active

    rows: list[InventoryImportRow] = []
    for row_number, row in enumerate(ws.iter_rows(min_row=2, max_col=11, values_only=True), start=2):
        padded = list(row) + [None] * (11 - len(row))
        (
            _no,
            faculty_name,
            sub_unit,
            room,
            inventory_number,
            uzasbo,
            inventory_type,
            model,
            status,
            internet_connection,
            responsible_person,
        ) = padded[:11]

        faculty_name_clean = _clean(faculty_name)
        if faculty_name_clean is None:
            continue

        rows.append(
            InventoryImportRow(
                row_number=row_number,
                faculty_name=faculty_name_clean,
                sub_unit=_clean(sub_unit),
                room=_clean(room),
                inventory_number=_clean(inventory_number),
                uzasbo=_clean(uzasbo),
                inventory_type=_clean(inventory_type),
                model=_clean(model),
                status=_normalize_status(status),
                internet_connection=_clean(internet_connection),
                responsible_person=_clean(responsible_person),
            )
        )
    return rows
