from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_full_name = State()
    waiting_faculty = State()


class ProfileChange(StatesGroup):
    waiting_faculty = State()


class NewTicket(StatesGroup):
    waiting_category = State()
    waiting_description = State()
    waiting_priority = State()
    waiting_attachment = State()
    confirm = State()


class CloseTicket(StatesGroup):
    waiting_comment = State()
    waiting_suspicious_comment = State()


class ReassignTicket(StatesGroup):
    waiting_target = State()
    waiting_reason = State()


class RatingFlow(StatesGroup):
    waiting_comment = State()
