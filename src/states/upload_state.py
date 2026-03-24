from aiogram.fsm.state import StatesGroup, State


class UploadState(StatesGroup):
    waiting_for_type = State()
    waiting_for_pdf = State()
    choosing_profile_mode = State()
    # Flow B: custom data entry during upload
    waiting_for_name = State()
    waiting_for_roll = State()
    waiting_for_course = State()
    waiting_for_semester = State()
    waiting_for_department = State()
    waiting_for_session = State()
    waiting_for_year = State()
    # Common
    waiting_for_subject = State()
    confirming = State()