import io
from collections.abc import Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.ticket import TicketOut

CATEGORY_LABELS_UZ = {
    "computer": "Kompyuter",
    "network": "Tarmoq/internet",
    "projector": "Proyektor",
    "power": "Elektr ta'minoti",
    "printer": "Printer",
    "software": "Dasturiy ta'minot",
    "other": "Boshqa",
}
PRIORITY_LABELS_UZ = {"urgent": "Shoshilinch", "normal": "Oddiy"}
STATUS_LABELS_UZ = {"open": "Ochiq", "in_progress": "Jarayonda", "closed": "Yopilgan"}


def generate_ticket_pdf(ticket: Ticket, creator: User, faculty_name: str, technician: User | None) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleUz", parent=styles["Title"], fontSize=14, leading=18)
    subtitle_style = ParagraphStyle("SubtitleUz", parent=styles["Normal"], fontSize=10, alignment=1, spaceAfter=12)

    elements = [
        Paragraph("Guliston davlat universiteti", title_style),
        Paragraph("Texnik yordam ma'lumotnomasi", subtitle_style),
        Spacer(1, 0.3 * cm),
    ]

    rows = [
        ["Ariza raqami:", ticket.ticket_number],
        ["FISH:", creator.full_name],
        ["Telefon:", creator.phone],
        ["Fakultet:", faculty_name],
        ["Muammo toifasi:", CATEGORY_LABELS_UZ.get(ticket.category.value, ticket.category.value)],
        ["Muhimlik darajasi:", PRIORITY_LABELS_UZ.get(ticket.priority.value, ticket.priority.value)],
        ["Muammo tavsifi:", ticket.description],
        ["Sana/vaqt:", ticket.created_at.strftime("%Y-%m-%d %H:%M") if ticket.created_at else "-"],
        ["Texnik xodim:", technician.full_name if technician else "-"],
        ["Holati:", STATUS_LABELS_UZ.get(ticket.status.value, ticket.status.value)],
        ["Yechim izohi:", ticket.resolution_comment or "-"],
    ]

    table = Table(rows, colWidths=[4.5 * cm, 11.5 * cm])
    table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()


def generate_tickets_list_pdf(tickets: Sequence[TicketOut]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleUz", parent=styles["Title"], fontSize=14, leading=18)
    cell_style = ParagraphStyle("CellUz", parent=styles["Normal"], fontSize=7.5, leading=9)

    elements = [
        Paragraph("Guliston davlat universiteti — Bildirishnomalar ro'yxati", title_style),
        Spacer(1, 0.3 * cm),
    ]

    header = [
        "Ariza №", "FISH", "Telefon", "Fakultet", "Toifa", "Muhimlik",
        "Holat", "Texnik xodim", "Yaratilgan", "Yopilgan", "Baho",
    ]
    rows = [header]
    for t in tickets:
        rows.append(
            [
                t.ticket_number,
                Paragraph(t.creator_full_name, cell_style),
                t.creator_phone,
                Paragraph(t.faculty_name, cell_style),
                CATEGORY_LABELS_UZ.get(t.category.value, t.category.value),
                PRIORITY_LABELS_UZ.get(t.priority.value, t.priority.value),
                STATUS_LABELS_UZ.get(t.status.value, t.status.value),
                Paragraph(t.technician_full_name or "-", cell_style),
                t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "-",
                t.closed_at.strftime("%Y-%m-%d %H:%M") if t.closed_at else "-",
                "★" * t.rating_stars if t.rating_stars else "-",
            ]
        )

    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()
