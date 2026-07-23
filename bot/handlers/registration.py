from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.enums import UserRole
from app.models.faculty import Faculty
from app.models.user import User

from bot.keyboards import faculty_keyboard, main_menu_keyboard, phone_request_keyboard, remove_keyboard
from bot.services.users import get_user_by_phone, get_user_by_telegram_id
from bot.states import ProfileChange, Registration

router = Router(name="registration")


def _menu_for(user: User):
    return main_menu_keyboard() if user.role == UserRole.FACULTY_STAFF else remove_keyboard()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    async with async_session_factory() as db:
        user = await get_user_by_telegram_id(db, message.from_user.id)

        if user is not None:
            if user.is_blocked:
                await message.answer("Hisobingiz bloklangan. Super Admin bilan bog'laning.")
                return
            await message.answer(f"Xush kelibsiz, {user.full_name}!", reply_markup=_menu_for(user))
            return

    await message.answer(
        "Assalomu alaykum! Botdan foydalanish uchun telefon raqamingizni yuboring.",
        reply_markup=phone_request_keyboard(),
    )


@router.message(F.contact)
async def handle_contact(message: Message, state: FSMContext) -> None:
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer("Iltimos, pastdagi tugma orqali o'zingizning kontaktingizni yuboring.")
        return

    phone = contact.phone_number

    async with async_session_factory() as db:
        user = await get_user_by_phone(db, phone)

        if user is not None:
            if user.telegram_id is not None and user.telegram_id != message.from_user.id:
                await message.answer(
                    "Bu telefon raqami allaqachon boshqa Telegram hisobiga bog'langan. "
                    "Super Admin bilan bog'laning.",
                    reply_markup=remove_keyboard(),
                )
                return
            if user.is_blocked:
                await message.answer(
                    "Hisobingiz bloklangan. Super Admin bilan bog'laning.", reply_markup=remove_keyboard()
                )
                return
            user.telegram_id = message.from_user.id
            await db.commit()
            await message.answer(
                f"Xush kelibsiz, {user.full_name}! Hisobingiz bog'landi.", reply_markup=_menu_for(user)
            )
            return

    await state.update_data(phone=phone)
    await state.set_state(Registration.waiting_full_name)
    await message.answer("FISH (Familiya Ism Sharifingiz)ni kiriting:", reply_markup=remove_keyboard())


@router.message(StateFilter(Registration.waiting_full_name))
async def handle_full_name(message: Message, state: FSMContext) -> None:
    full_name = (message.text or "").strip()
    if not full_name:
        await message.answer("Iltimos, FISHni matn ko'rinishida kiriting.")
        return
    await state.update_data(full_name=full_name)

    async with async_session_factory() as db:
        result = await db.execute(select(Faculty).order_by(Faculty.name))
        faculties = list(result.scalars().all())

    await state.set_state(Registration.waiting_faculty)
    await message.answer("Fakultetingizni tanlang:", reply_markup=faculty_keyboard(faculties))


@router.callback_query(StateFilter(Registration.waiting_faculty), F.data.startswith("faculty:"))
async def handle_registration_faculty(callback: CallbackQuery, state: FSMContext) -> None:
    faculty_id = int(callback.data.split(":")[1])
    data = await state.get_data()

    async with async_session_factory() as db:
        db.add(
            User(
                telegram_id=callback.from_user.id,
                full_name=data["full_name"],
                phone=data["phone"],
                faculty_id=faculty_id,
                role=UserRole.FACULTY_STAFF,
            )
        )
        await db.commit()

    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Ro'yxatdan muvaffaqiyatli o'tdingiz!", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.message(Command("profil"))
async def cmd_profile(message: Message, state: FSMContext) -> None:
    async with async_session_factory() as db:
        user = await get_user_by_telegram_id(db, message.from_user.id)
        if user is None:
            await message.answer("Avval /start orqali ro'yxatdan o'ting.")
            return
        if user.role != UserRole.FACULTY_STAFF:
            await message.answer(f"FISH: {user.full_name}\nTelefon: {user.phone}\nRol: {user.role.value}")
            return

        result = await db.execute(select(Faculty).order_by(Faculty.name))
        faculties = list(result.scalars().all())

    await state.set_state(ProfileChange.waiting_faculty)
    await message.answer("Yangi fakultetingizni tanlang:", reply_markup=faculty_keyboard(faculties))


@router.callback_query(StateFilter(ProfileChange.waiting_faculty), F.data.startswith("faculty:"))
async def handle_profile_faculty(callback: CallbackQuery, state: FSMContext) -> None:
    faculty_id = int(callback.data.split(":")[1])

    async with async_session_factory() as db:
        user = await get_user_by_telegram_id(db, callback.from_user.id)
        if user is None:
            await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
            return
        user.faculty_id = faculty_id
        await db.commit()

    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Fakultet muvaffaqiyatli o'zgartirildi.")
    await callback.answer()
