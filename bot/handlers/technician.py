import asyncio

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.enums import TicketStatus, UserRole
from app.models.faculty import Faculty
from app.models.ticket import Ticket
from app.models.user import User
from app.services.pdf_generator import generate_ticket_pdf

from bot.keyboards import (
    INVENTORY_PAGE_SIZE,
    inventory_browse_keyboard,
    inventory_picker_keyboard,
    suspicious_keyboard,
    technician_choice_keyboard,
    ticket_actions_keyboard,
)
from bot.services.inventory import count_repairs, find_inventory_item, list_inventory_page
from bot.services.tickets import (
    accept_ticket,
    can_close_ticket,
    close_ticket,
    get_faculty_technicians,
    is_technician_assigned,
    notify_reassignment,
    notify_ticket_accepted,
    notify_ticket_closed,
    reassign_ticket,
)
from bot.services.users import get_user_by_telegram_id
from bot.states import CloseTicket, ReassignTicket

router = Router(name="technician")


async def _get_ticket(db: AsyncSession, ticket_id: int) -> Ticket | None:
    return await db.get(Ticket, ticket_id)


@router.callback_query(F.data.startswith("accept:"))
async def handle_accept(callback: CallbackQuery) -> None:
    ticket_id = int(callback.data.split(":")[1])

    async with async_session_factory() as db:
        technician = await get_user_by_telegram_id(db, callback.from_user.id)
        ticket = await _get_ticket(db, ticket_id)
        if technician is None or ticket is None:
            await callback.answer("Topilmadi", show_alert=True)
            return
        if technician.role not in (
            UserRole.TECHNICIAN_MAIN,
            UserRole.TECHNICIAN_BACKUP,
        ) or not await is_technician_assigned(db, technician.id, ticket.faculty_id):
            await callback.answer("Sizda bu huquq yo'q", show_alert=True)
            return
        if ticket.status != TicketStatus.OPEN:
            await callback.answer("Bu ariza allaqachon qabul qilingan", show_alert=True)
            return

        accepted = await accept_ticket(db, ticket, technician)
        if not accepted:
            await callback.answer("Bu ariza allaqachon boshqa texnik xodim tomonidan qabul qilingan", show_alert=True)
            await callback.message.edit_reply_markup(reply_markup=None)
            return
        creator = await db.get(User, ticket.created_by_user_id)
        await notify_ticket_accepted(callback.bot, ticket, creator)

    await callback.message.edit_reply_markup(reply_markup=ticket_actions_keyboard(ticket_id))
    await callback.answer("Qabul qilindi")


@router.callback_query(F.data.startswith("close:"))
async def handle_close_start(callback: CallbackQuery, state: FSMContext) -> None:
    ticket_id = int(callback.data.split(":")[1])

    async with async_session_factory() as db:
        technician = await get_user_by_telegram_id(db, callback.from_user.id)
        ticket = await _get_ticket(db, ticket_id)
        if technician is None or ticket is None or not await can_close_ticket(db, ticket, technician):
            await callback.answer("Sizda bu huquq yo'q", show_alert=True)
            return

    await state.update_data(ticket_id=ticket_id)
    await state.set_state(CloseTicket.waiting_inventory_number)
    await callback.message.answer(
        "Ta'mirlangan qurilmaning inventar raqamini kiriting, yoki ro'yxatdan tanlang:",
        reply_markup=inventory_browse_keyboard(ticket_id),
    )
    await callback.answer()


@router.message(StateFilter(CloseTicket.waiting_inventory_number))
async def handle_close_inventory_number(message: Message, state: FSMContext) -> None:
    number = (message.text or "").strip()
    data = await state.get_data()

    async with async_session_factory() as db:
        ticket = await _get_ticket(db, data["ticket_id"])
        if ticket is None:
            await state.clear()
            await message.answer("Ariza topilmadi.")
            return
        item = await find_inventory_item(db, ticket.faculty_id, number)

    if item is None:
        await message.answer(
            "Bu raqam bilan inventar topilmadi. Iltimos, raqamni tekshirib qayta kiriting "
            "yoki ro'yxatdan tanlang:",
            reply_markup=inventory_browse_keyboard(data["ticket_id"]),
        )
        return

    await state.update_data(inventory_item_id=item.id)
    await state.set_state(CloseTicket.waiting_comment)
    await message.answer("Yechim izohini yozing (yoki '-' yuboring):")


async def _render_inventory_page(message: Message, ticket_id: int, page: int, edit: bool) -> None:
    async with async_session_factory() as db:
        ticket = await _get_ticket(db, ticket_id)
        if ticket is None:
            return
        items, total = await list_inventory_page(
            db, ticket.faculty_id, page * INVENTORY_PAGE_SIZE, INVENTORY_PAGE_SIZE
        )

    if not items:
        text = "Bu yo'nalishda hali inventar ro'yxatga olinmagan. Iltimos, raqamni qo'lda kiriting yoki admin panelda qo'shing."
        keyboard = None
    else:
        text = "Qurilmani tanlang:"
        keyboard = inventory_picker_keyboard(items, ticket_id, page, total)

    if edit:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("invlist:"))
async def handle_inventory_list(callback: CallbackQuery, state: FSMContext) -> None:
    _, ticket_id_str, page_str = callback.data.split(":")
    ticket_id = int(ticket_id_str)
    data = await state.get_data()
    if data.get("ticket_id") != ticket_id:
        await callback.answer("Amal muddati tugagan, qaytadan boshlang", show_alert=True)
        return
    await _render_inventory_page(callback.message, ticket_id, int(page_str), edit=False)
    await callback.answer()


@router.callback_query(F.data.startswith("invpage:"))
async def handle_inventory_page(callback: CallbackQuery, state: FSMContext) -> None:
    _, ticket_id_str, page_str = callback.data.split(":")
    ticket_id = int(ticket_id_str)
    data = await state.get_data()
    if data.get("ticket_id") != ticket_id:
        await callback.answer("Amal muddati tugagan, qaytadan boshlang", show_alert=True)
        return
    await _render_inventory_page(callback.message, ticket_id, int(page_str), edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("invitem:"))
async def handle_inventory_item_choice(callback: CallbackQuery, state: FSMContext) -> None:
    _, ticket_id_str, item_id_str = callback.data.split(":")
    ticket_id = int(ticket_id_str)
    data = await state.get_data()
    if data.get("ticket_id") != ticket_id:
        await callback.answer("Amal muddati tugagan, qaytadan boshlang", show_alert=True)
        return

    await state.update_data(inventory_item_id=int(item_id_str))
    await state.set_state(CloseTicket.waiting_comment)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Yechim izohini yozing (yoki '-' yuboring):")
    await callback.answer()


@router.callback_query(F.data == "noop")
async def handle_noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()


@router.message(StateFilter(CloseTicket.waiting_comment))
async def handle_close_comment(message: Message, state: FSMContext) -> None:
    comment = (message.text or "").strip()
    await state.update_data(resolution_comment=None if comment == "-" else comment)
    data = await state.get_data()
    await message.answer("Bu chaqiruv shubhalimi?", reply_markup=suspicious_keyboard(data["ticket_id"]))


async def _do_close(
    bot, state: FSMContext, telegram_id: int, ticket_id: int, is_suspicious: bool, suspicious_comment: str | None
) -> Ticket | None:
    data = await state.get_data()
    async with async_session_factory() as db:
        technician = await get_user_by_telegram_id(db, telegram_id)
        ticket = await _get_ticket(db, ticket_id)
        if (
            technician is None
            or ticket is None
            or not await can_close_ticket(db, ticket, technician)
            or data.get("inventory_item_id") is None
        ):
            await state.clear()
            return None
        await close_ticket(
            db, ticket, data.get("resolution_comment"), is_suspicious, suspicious_comment, data["inventory_item_id"]
        )
        creator = await db.get(User, ticket.created_by_user_id)
        await notify_ticket_closed(bot, ticket, creator)
        repair_count = await count_repairs(db, data["inventory_item_id"])
    await state.clear()
    ticket.repair_count = repair_count
    return ticket


@router.callback_query(F.data.startswith("suspicious:"))
async def handle_suspicious_choice(callback: CallbackQuery, state: FSMContext) -> None:
    _, choice, ticket_id_str = callback.data.split(":")
    ticket_id = int(ticket_id_str)
    data = await state.get_data()
    if data.get("ticket_id") != ticket_id:
        await callback.answer("Amal muddati tugagan, qaytadan boshlang", show_alert=True)
        return
    await callback.message.edit_reply_markup(reply_markup=None)

    if choice == "yes":
        await state.update_data(ticket_id=ticket_id)
        await state.set_state(CloseTicket.waiting_suspicious_comment)
        await callback.message.answer("Shubhali chaqiruv sababini yozing:")
        await callback.answer()
        return

    ticket = await _do_close(callback.bot, state, callback.from_user.id, ticket_id, False, None)
    if ticket is None:
        await callback.message.answer("Amalni bajarib bo'lmadi: ariza topilmadi yoki huquqingiz yo'q.")
        await callback.answer()
        return
    await callback.message.answer(
        f"✅ Ariza #{ticket.ticket_number} yopildi. Bu qurilma jami {ticket.repair_count} marta ta'mirlangan."
    )
    await callback.answer()


@router.message(StateFilter(CloseTicket.waiting_suspicious_comment))
async def handle_suspicious_comment(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    ticket = await _do_close(message.bot, state, message.from_user.id, data["ticket_id"], True, message.text)
    if ticket is None:
        await message.answer("Amalni bajarib bo'lmadi: ariza topilmadi yoki huquqingiz yo'q.")
        return
    await message.answer(
        f"✅ Ariza #{ticket.ticket_number} yopildi. Bu qurilma jami {ticket.repair_count} marta ta'mirlangan."
    )


@router.callback_query(F.data.startswith("reassign:"))
async def handle_reassign_start(callback: CallbackQuery, state: FSMContext) -> None:
    ticket_id = int(callback.data.split(":")[1])

    async with async_session_factory() as db:
        technician = await get_user_by_telegram_id(db, callback.from_user.id)
        ticket = await _get_ticket(db, ticket_id)
        if (
            technician is None
            or ticket is None
            or technician.role not in (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP)
            or not await is_technician_assigned(db, technician.id, ticket.faculty_id)
        ):
            await callback.answer("Sizda bu huquq yo'q", show_alert=True)
            return
        candidates = await get_faculty_technicians(db, ticket.faculty_id, exclude_user_id=technician.id)

    if not candidates:
        await callback.answer("Boshqa texnik xodim topilmadi", show_alert=True)
        return

    await state.update_data(ticket_id=ticket_id)
    await callback.message.answer(
        "Kimga qayta yo'naltirmoqchisiz?", reply_markup=technician_choice_keyboard(candidates, ticket_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("reassign_to:"))
async def handle_reassign_target(callback: CallbackQuery, state: FSMContext) -> None:
    _, ticket_id_str, target_id_str = callback.data.split(":")
    ticket_id = int(ticket_id_str)
    data = await state.get_data()
    if data.get("ticket_id") != ticket_id:
        await callback.answer("Amal muddati tugagan, qaytadan boshlang", show_alert=True)
        return

    await state.update_data(target_technician_id=int(target_id_str))
    await state.set_state(ReassignTicket.waiting_reason)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Qayta yo'naltirish sababini yozing:")
    await callback.answer()


@router.message(StateFilter(ReassignTicket.waiting_reason))
async def handle_reassign_reason(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    reason = (message.text or "").strip()

    async with async_session_factory() as db:
        from_technician = await get_user_by_telegram_id(db, message.from_user.id)
        ticket = await _get_ticket(db, data["ticket_id"])
        to_technician = await db.get(User, data["target_technician_id"])
        if (
            from_technician is None
            or ticket is None
            or to_technician is None
            or from_technician.role not in (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP)
            or not await is_technician_assigned(db, from_technician.id, ticket.faculty_id)
            or not await is_technician_assigned(db, to_technician.id, ticket.faculty_id)
        ):
            await state.clear()
            await message.answer("Amalni bajarib bo'lmadi: ariza topilmadi yoki huquqingiz yo'q.")
            return
        await reassign_ticket(db, ticket, from_technician, to_technician, reason)
        await notify_reassignment(message.bot, db, ticket, to_technician, reason)

    await state.clear()
    await message.answer(f"✅ Ariza #{ticket.ticket_number} {to_technician.full_name}ga qayta yo'naltirildi.")


@router.callback_query(F.data.startswith("pdf:"))
async def handle_pdf(callback: CallbackQuery) -> None:
    ticket_id = int(callback.data.split(":")[1])

    async with async_session_factory() as db:
        technician = await get_user_by_telegram_id(db, callback.from_user.id)
        ticket = await _get_ticket(db, ticket_id)
        if (
            technician is None
            or ticket is None
            or technician.role not in (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP, UserRole.SUPER_ADMIN)
            or (
                technician.role != UserRole.SUPER_ADMIN
                and not await is_technician_assigned(db, technician.id, ticket.faculty_id)
            )
        ):
            await callback.answer("Sizda bu huquq yo'q", show_alert=True)
            return

        creator = await db.get(User, ticket.created_by_user_id)
        faculty = await db.get(Faculty, ticket.faculty_id)
        assigned = await db.get(User, ticket.assigned_technician_id) if ticket.assigned_technician_id else None

        pdf_bytes = await asyncio.to_thread(generate_ticket_pdf, ticket, creator, faculty.name, assigned)

    await callback.message.answer_document(
        BufferedInputFile(pdf_bytes, filename=f"{ticket.ticket_number}.pdf"),
    )
    await callback.answer()
