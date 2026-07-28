from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.enums import AttachmentType, TicketCategory, TicketPriority, UserRole
from app.models.ticket import Ticket
from app.models.user import User

from bot.keyboards import (
    category_keyboard,
    confirm_ticket_keyboard,
    main_menu_keyboard,
    priority_keyboard,
    skip_attachment_keyboard,
)
from bot.services.files import save_telegram_file
from bot.services.tickets import (
    CATEGORY_LABELS_UZ,
    PRIORITY_LABELS_UZ,
    count_open_tickets_for_faculty,
    create_ticket,
    notify_new_ticket,
)
from bot.services.users import get_user_by_telegram_id
from bot.states import NewTicket

router = Router(name="tickets")

HELP_TEXT = (
    "ℹ️ Yordam\n\n"
    "🆕 Yangi ariza — texnik muammo haqida ariza yuborish\n"
    "📋 Mening arizalarim — yuborgan arizalaringiz holati\n"
    "👤 Profil — fakultetingizni ko'rish/o'zgartirish\n"
    "/start — botni qayta ishga tushirish"
)

STATUS_LABELS_UZ = {"open": "Ochiq", "in_progress": "Jarayonda", "closed": "Yopilgan"}


async def _require_active_faculty_staff(message: Message) -> User | None:
    async with async_session_factory() as db:
        user = await get_user_by_telegram_id(db, message.from_user.id)
    if user is None:
        await message.answer("Avval /start orqali ro'yxatdan o'ting.")
        return None
    if user.is_blocked:
        await message.answer("Hisobingiz bloklangan. Super Admin bilan bog'laning.")
        return None
    if user.role != UserRole.FACULTY_STAFF:
        await message.answer("Bu buyruq faqat fakultet xodimlari uchun.")
        return None
    return user


@router.message(F.text == "🆕 Yangi ariza")
async def start_new_ticket(message: Message, state: FSMContext) -> None:
    user = await _require_active_faculty_staff(message)
    if user is None:
        return
    await state.set_state(NewTicket.waiting_category)
    await message.answer("Muammo toifasini tanlang:", reply_markup=category_keyboard())


@router.callback_query(StateFilter(NewTicket.waiting_category), F.data.startswith("category:"))
async def handle_category(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.split(":")[1]
    await state.update_data(category=category)
    await state.set_state(NewTicket.waiting_description)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Muammoni qisqacha tavsiflab bering:")
    await callback.answer()


@router.message(StateFilter(NewTicket.waiting_description))
async def handle_description(message: Message, state: FSMContext) -> None:
    description = (message.text or "").strip()
    if not description:
        await message.answer("Iltimos, muammoni matn ko'rinishida yozing.")
        return
    await state.update_data(description=description)
    await state.set_state(NewTicket.waiting_priority)
    await message.answer("Muhimlik darajasini tanlang:", reply_markup=priority_keyboard())


@router.callback_query(StateFilter(NewTicket.waiting_priority), F.data.startswith("priority:"))
async def handle_priority(callback: CallbackQuery, state: FSMContext) -> None:
    priority = callback.data.split(":")[1]
    await state.update_data(priority=priority, attachments=[])
    await state.set_state(NewTicket.waiting_attachment)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Muammoga oid rasm yoki video biriktirishingiz mumkin (ixtiyoriy):",
        reply_markup=skip_attachment_keyboard(),
    )
    await callback.answer()


async def _show_confirmation(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(NewTicket.confirm)
    text = (
        "Arizangizni tasdiqlang:\n\n"
        f"📝 Tavsif: {data['description']}\n"
        f"🏷 Toifa: {CATEGORY_LABELS_UZ.get(data['category'], data['category'])}\n"
        f"⚡ Muhimlik: {PRIORITY_LABELS_UZ.get(data['priority'], data['priority'])}\n"
        f"📎 Biriktirilgan fayllar: {len(data.get('attachments', []))}"
    )
    await message.answer(text, reply_markup=confirm_ticket_keyboard())


@router.message(StateFilter(NewTicket.waiting_attachment), F.photo)
async def handle_photo_attachment(message: Message, state: FSMContext) -> None:
    file_id = message.photo[-1].file_id
    path = await save_telegram_file(message, file_id, ".jpg")
    data = await state.get_data()
    attachments = data.get("attachments", [])
    attachments.append((path, AttachmentType.PHOTO.value))
    await state.update_data(attachments=attachments)
    await _show_confirmation(message, state)


@router.message(StateFilter(NewTicket.waiting_attachment), F.video)
async def handle_video_attachment(message: Message, state: FSMContext) -> None:
    file_id = message.video.file_id
    path = await save_telegram_file(message, file_id, ".mp4")
    data = await state.get_data()
    attachments = data.get("attachments", [])
    attachments.append((path, AttachmentType.VIDEO.value))
    await state.update_data(attachments=attachments)
    await _show_confirmation(message, state)


@router.callback_query(StateFilter(NewTicket.waiting_attachment), F.data == "attachment:skip")
async def handle_skip_attachment(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)
    await _show_confirmation(callback.message, state)
    await callback.answer()


@router.callback_query(StateFilter(NewTicket.confirm), F.data == "ticket:cancel")
async def handle_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Ariza bekor qilindi.", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(StateFilter(NewTicket.confirm), F.data == "ticket:submit")
async def handle_submit(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()

    async with async_session_factory() as db:
        user = await get_user_by_telegram_id(db, callback.from_user.id)
        if user is None or user.is_blocked:
            await callback.answer("Xatolik yuz berdi.", show_alert=True)
            await state.clear()
            return

        attachments = [(path, AttachmentType(t)) for path, t in data.get("attachments", [])]
        ticket = await create_ticket(
            db,
            created_by=user,
            description=data["description"],
            category=TicketCategory(data["category"]),
            priority=TicketPriority(data["priority"]),
            attachments=attachments,
        )
        open_count = await count_open_tickets_for_faculty(db, user.faculty_id)
        await notify_new_ticket(callback.bot, db, ticket)

    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"✅ Arizangiz qabul qilindi!\nAriza raqami: {ticket.ticket_number}\n"
        f"Joriy ochiq arizalar soni: {open_count}",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.message(Command("yordam"))
@router.message(F.text == "ℹ️ Yordam")
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("mening_arizalarim"))
@router.message(F.text == "📋 Mening arizalarim")
async def cmd_my_tickets(message: Message) -> None:
    async with async_session_factory() as db:
        user = await get_user_by_telegram_id(db, message.from_user.id)
        if user is None:
            await message.answer("Avval /start orqali ro'yxatdan o'ting.")
            return

        result = await db.execute(
            select(Ticket).where(Ticket.created_by_user_id == user.id).order_by(Ticket.created_at.desc())
        )
        tickets = list(result.scalars().all())

        if not tickets:
            await message.answer("Sizda hali arizalar yo'q.")
            return

        open_count = await count_open_tickets_for_faculty(db, user.faculty_id) if user.faculty_id else 0

        lines = [f"Fakultetdagi joriy ochiq arizalar: {open_count}\n"]
        for t in tickets:
            lines.append(f"#{t.ticket_number} — {STATUS_LABELS_UZ.get(t.status.value, t.status.value)}")

    await message.answer("\n".join(lines))
