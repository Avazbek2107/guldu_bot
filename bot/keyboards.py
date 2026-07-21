from aiogram.types import (
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

CATEGORY_LABELS = {
    "computer": "🖥 Kompyuter",
    "network": "🌐 Tarmoq/internet",
    "projector": "📽 Proyektor",
    "power": "🔌 Elektr ta'minoti",
    "printer": "🖨 Printer",
    "software": "💿 Dasturiy ta'minot",
    "other": "❓ Boshqa",
}

PRIORITY_LABELS = {
    "urgent": "🔴 Shoshilinch",
    "normal": "🟢 Oddiy",
}


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🆕 Yangi ariza")],
            [KeyboardButton(text="📋 Mening arizalarim"), KeyboardButton(text="👤 Profil")],
            [KeyboardButton(text="ℹ️ Yordam")],
        ],
        resize_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def faculty_keyboard(faculties: list, callback_prefix: str = "faculty") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for faculty in faculties:
        builder.button(text=faculty.name, callback_data=f"{callback_prefix}:{faculty.id}")
    builder.adjust(1)
    return builder.as_markup()


def category_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for value, label in CATEGORY_LABELS.items():
        builder.button(text=label, callback_data=f"category:{value}")
    builder.adjust(2)
    return builder.as_markup()


def priority_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for value, label in PRIORITY_LABELS.items():
        builder.button(text=label, callback_data=f"priority:{value}")
    builder.adjust(1)
    return builder.as_markup()


def skip_attachment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ O'tkazib yuborish", callback_data="attachment:skip")
    return builder.as_markup()


def confirm_ticket_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yuborish", callback_data="ticket:submit")
    builder.button(text="❌ Bekor qilish", callback_data="ticket:cancel")
    builder.adjust(2)
    return builder.as_markup()


def accept_ticket_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Qabul qildim", callback_data=f"accept:{ticket_id}")
    return builder.as_markup()


def ticket_actions_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yopish", callback_data=f"close:{ticket_id}")
    builder.button(text="↪️ Qayta yo'naltirish", callback_data=f"reassign:{ticket_id}")
    builder.adjust(1)
    return builder.as_markup()


def suspicious_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Ha", callback_data=f"suspicious:yes:{ticket_id}")
    builder.button(text="Yo'q", callback_data=f"suspicious:no:{ticket_id}")
    builder.adjust(2)
    return builder.as_markup()


def rating_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for stars in range(1, 6):
        builder.button(text="⭐" * stars, callback_data=f"rate:{ticket_id}:{stars}")
    builder.adjust(1)
    return builder.as_markup()


def technician_choice_keyboard(technicians: list, ticket_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for tech in technicians:
        builder.button(text=tech.full_name, callback_data=f"reassign_to:{ticket_id}:{tech.id}")
    builder.adjust(1)
    return builder.as_markup()
