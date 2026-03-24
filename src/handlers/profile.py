"""Profile handler – view / create user profile."""
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from src.states.profile_state import ProfileState
from src.keyboards import inline
from src.keyboards.inline import (
    needs_department,
    course_kb, department_kb, semester_kb,
    profile_confirm_kb, back_kb, profile_view_kb,
)
from src.locales import get_langs
from src.services import db_service

app = Router()


async def _lang(tid: int) -> str:
    return await db_service.get_user_language(tid)


# ─── Entry: "Profile" button ─────────────────────────────────

@app.callback_query(lambda c: c.data == "profile")
async def profile_entry(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)

    user = await db_service.get_user(callback.from_user.id)

    if user and user.get("name"):
        # Profile exists → show it
        dept = user.get("department") or "N/A"
        await callback.message.edit_text(
            f"{_['profile']['title']}\n\n"
            f"{_['profile']['name']}: {user['name']}\n"
            f"{_['profile']['roll_no']}: {user.get('roll_no', 'N/A')}\n"
            f"{_['profile']['course']}: {user.get('course', 'N/A')}\n"
            f"{_['profile']['department']}: {dept}\n"
            f"{_['profile']['semester']}: {user.get('semester', 'N/A')}\n"
            f"{_['profile']['session']}: {user.get('session', 'N/A')}",
            reply_markup=profile_view_kb(),
            parse_mode="html",
        )
    else:
        # Profile doesn't exist → start creation
        await callback.message.edit_text(
            _["profile"]["not_exists"] + "\n" + _["profile"]["ask_name"],
            parse_mode="html",
        )
        await state.set_state(ProfileState.waiting_for_name)

    await callback.answer()


@app.callback_query(lambda c: c.data == "edit_profile")
async def profile_edit(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)
    await state.clear()
    await callback.message.edit_text(
        _["profile"]["ask_name"],
        parse_mode="html",
    )
    await state.set_state(ProfileState.waiting_for_name)
    await callback.answer()


# ─── Step 1: Name ─────────────────────────────────────────────

@app.message(StateFilter(ProfileState.waiting_for_name))
async def profile_get_name(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    _ = get_langs(lang)

    if not message.text or len(message.text.strip()) < 2:
        return await message.answer(_["errors"]["too_short"], parse_mode="html")

    await state.update_data(name=message.text.strip())
    await message.answer(_["profile"]["ask_roll"], parse_mode="html")
    await state.set_state(ProfileState.waiting_for_roll)


# ─── Step 2: Roll No ─────────────────────────────────────────

@app.message(StateFilter(ProfileState.waiting_for_roll))
async def profile_get_roll(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    _ = get_langs(lang)

    if not message.text or len(message.text.strip()) < 2:
        return await message.answer(_["errors"]["too_short"], parse_mode="html")

    await state.update_data(roll_no=message.text.strip())
    await message.answer(_["profile"]["ask_course"], reply_markup=course_kb(), parse_mode="html")
    await state.set_state(ProfileState.waiting_for_course)


# ─── Step 3: Course ──────────────────────────────────────────

@app.callback_query(StateFilter(ProfileState.waiting_for_course), lambda c: c.data.startswith("course_"))
async def profile_get_course(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)

    course_key = callback.data.split("_", 1)[1]
    await state.update_data(course=course_key)

    await callback.message.edit_text(
        _["profile"]["ask_semester"], reply_markup=semester_kb(course_key), parse_mode="html"
    )
    await state.set_state(ProfileState.waiting_for_semester)
    await callback.answer()


# ─── Step 4: Semester ─────────────────────────────────────────

@app.callback_query(StateFilter(ProfileState.waiting_for_semester), lambda c: c.data.startswith("sem_"))
async def profile_get_semester(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)

    sem_num = int(callback.data.split("_")[1])
    await state.update_data(semester=str(sem_num))

    data = await state.get_data()
    course_key = data.get("course", "BTECH")

    if needs_department(course_key):
        await callback.message.edit_text(
            _["profile"]["ask_department"], reply_markup=department_kb(course_key, sem_num), parse_mode="html"
        )
        await state.set_state(ProfileState.waiting_for_department)
    else:
        await state.update_data(department=None)
        await callback.message.edit_text(_["profile"]["ask_session"], parse_mode="html")
        await state.set_state(ProfileState.waiting_for_session)

    await callback.answer()


# ─── Step 5: Department (conditional) ────────────────────────

@app.callback_query(StateFilter(ProfileState.waiting_for_department), lambda c: c.data.startswith("dept_"))
async def profile_get_department(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)

    dept_key = callback.data.split("_", 1)[1]
    await state.update_data(department=dept_key)

    await callback.message.edit_text(_["profile"]["ask_session"], parse_mode="html")
    await state.set_state(ProfileState.waiting_for_session)
    await callback.answer()





# ─── Step 6: Session ─────────────────────────────────────────

@app.message(StateFilter(ProfileState.waiting_for_session))
async def profile_get_session(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    _ = get_langs(lang)

    if not message.text or len(message.text.strip()) < 3:
        return await message.answer(_["errors"]["too_short"], parse_mode="html")

    await state.update_data(session=message.text.strip())
    data = await state.get_data()

    # Show confirmation screen
    await message.answer(
        _["profile"]["confirm"].format(
            name=data["name"],
            roll_no=data["roll_no"],
            course=data["course"],
            department=data.get("department") or "N/A",
            semester=data["semester"],
            session=data["session"],
        ),
        reply_markup=profile_confirm_kb(),
        parse_mode="html",
    )
    await state.set_state(ProfileState.confirming)


# ─── Confirm / Re-enter ──────────────────────────────────────

@app.callback_query(StateFilter(ProfileState.confirming), lambda c: c.data == "profile_confirm")
async def profile_confirm(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)

    data = await state.get_data()
    await db_service.create_user(
        telegram_id=callback.from_user.id,
        name=data["name"],
        roll_no=data["roll_no"],
        course=data["course"],
        department=data.get("department"),
        semester=data["semester"],
        session=data["session"],
        language=lang,
    )

    await callback.message.edit_text(_["profile"]["saved"], parse_mode="html")
    await state.clear()
    await callback.answer()


@app.callback_query(StateFilter(ProfileState.confirming), lambda c: c.data == "profile_reenter")
async def profile_reenter(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)

    await state.clear()
    await callback.message.edit_text(
        _["profile"]["reenter"] + "\n" + _["profile"]["ask_name"],
        parse_mode="html",
    )
    await state.set_state(ProfileState.waiting_for_name)
    await callback.answer()