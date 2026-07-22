import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.ticket import Ticket
from app.models.user import User

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
