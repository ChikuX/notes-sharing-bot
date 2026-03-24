from aiogram.fsm.state import StatesGroup, State


class ProfileState(StatesGroup):
    waiting_for_name = State()
    waiting_for_roll = State()
    waiting_for_course = State()
    waiting_for_semester = State()
    waiting_for_department = State()
    waiting_for_session = State()
    confirming = State()
