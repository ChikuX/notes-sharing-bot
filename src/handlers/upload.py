"""Upload handler – full upload FSM flow.

User confirm does NOT touch DB or storage.
It only sends the PDF + metadata to the admin channel.
"""
import uuid
import logging
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from src.states.upload_state import UploadState
from src.keyboards import inline
from src.keyboards.inline import (
    needs_department,
    course_kb, department_kb, semester_kb,
    profile_choice_kb, confirm_kb, profile_or_back_kb, upload_type_kb
)
from src.locales import get_langs
from src.services import db_service, submissions
from src.core.bot import bot
from src.core.config import config

app = Router()
log = logging.getLogger(__name__)


async def _lang(tid: int) -> str:
    return await db_service.get_user_language(tid)


# ─── Entry: "Upload Notes" button ────────────────────────────

@app.callback_query(lambda c: c.data == "upload")
async def upload_entry(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)

    await callback.message.edit_text(_["upload"]["ask_type"], reply_markup=upload_type_kb(), parse_mode="html")
    await state.set_state(UploadState.waiting_for_type)
    await callback.answer()

@app.callback_query(StateFilter(UploadState.waiting_for_type), lambda c: c.data in ["type_notes", "type_pyqs"])
async def upload_type_selection(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)
    
    item_type = "notes" if callback.data == "type_notes" else "pyqs"
    await state.update_data(item_type=item_type)

    # Check daily upload limit (max 5 per 24 hours)
    print("ADMINS: ", config.ADMIN_IDS)
    if callback.from_user.id not in config.ADMIN_IDS:
        daily_count = await db_service.get_daily_upload_count(callback.from_user.id)
        if daily_count >= 5:
            await callback.message.edit_text(_["upload"]["limit_reached"], parse_mode="html")
            await callback.answer()
            return

    # Pre-check: profile must exist
    user = await db_service.get_user(callback.from_user.id)
    if not user or not user.get("name"):
        await callback.message.edit_text(
            _["upload"]["need_profile"],
            reply_markup=profile_or_back_kb(),
            parse_mode="html",
        )
        await callback.answer()
        return

    await state.update_data(user_profile=dict(user))
    await callback.message.edit_text(_["upload"]["send_pdf"], parse_mode="html")
    await state.set_state(UploadState.waiting_for_pdf)
    await callback.answer()


# ─── Step 1: Receive PDF ─────────────────────────────────────

@app.message(StateFilter(UploadState.waiting_for_pdf))
async def handle_pdf(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    _ = get_langs(lang)

    if not message.document:
        return await message.answer(_["upload"]["no_document"], parse_mode="html")

    if message.document.mime_type != "application/pdf":
        return await message.answer(_["upload"]["not_pdf"], parse_mode="html")

    if message.document.file_size > 20 * 1024 * 1024:
        return await message.answer(_["upload"]["too_large"], parse_mode="html")

    await state.update_data(file_id=message.document.file_id)

    data = await state.get_data()
    profile = data.get("user_profile", {})

    await message.answer(
        _["upload"]["use_profile"].format(
            name=profile.get("name", "N/A"),
            roll_no=profile.get("roll_no", "N/A"),
            course=profile.get("course", "N/A"),
            department=profile.get("department") or "N/A",
            semester=profile.get("semester", "N/A"),
            session=profile.get("session", "N/A"),
        ),
        reply_markup=profile_choice_kb(),
        parse_mode="html",
    )
    await state.set_state(UploadState.choosing_profile_mode)


# ─── Step 2: Profile choice ──────────────────────────────────

@app.callback_query(StateFilter(UploadState.choosing_profile_mode), lambda c: c.data == "use_profile")
async def use_existing_profile(callback: CallbackQuery, state: FSMContext):
    """Flow A: use existing profile data → ask subject only."""
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)

    data = await state.get_data()
    profile = data["user_profile"]
    await state.update_data(
        display_name=profile.get("name") or "",
        display_roll=profile.get("roll_no") or "",
        display_course=profile.get("course") or "",
        display_department=profile.get("department"),
        display_semester=profile.get("semester") or "",
        display_session=profile.get("session") or "",
    )

    item_type = data.get("item_type", "notes")
    if item_type == "pyqs":
        await callback.message.edit_text(_["upload"]["ask_year"], parse_mode="html")
        await state.set_state(UploadState.waiting_for_year)
    else:
        await callback.message.edit_text(_["upload"]["ask_subject"], parse_mode="html")
        await state.set_state(UploadState.waiting_for_subject)
    await callback.answer()


@app.callback_query(StateFilter(UploadState.choosing_profile_mode), lambda c: c.data == "change_profile")
async def custom_data_entry(callback: CallbackQuery, state: FSMContext):
    """Flow B: enter custom data for this upload."""
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)

    await callback.message.edit_text(_["upload"]["ask_name"], parse_mode="html")
    await state.set_state(UploadState.waiting_for_name)
    await callback.answer()


# ─── Flow B: Custom data entry steps ─────────────────────────

@app.message(StateFilter(UploadState.waiting_for_name))
async def upload_get_name(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    _ = get_langs(lang)

    if not message.text or len(message.text.strip()) < 2:
        return await message.answer(_["errors"]["too_short"], parse_mode="html")

    await state.update_data(display_name=message.text.strip())
    await message.answer(_["upload"]["ask_roll"], parse_mode="html")
    await state.set_state(UploadState.waiting_for_roll)


@app.message(StateFilter(UploadState.waiting_for_roll))
async def upload_get_roll(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    _ = get_langs(lang)

    if not message.text or len(message.text.strip()) < 2:
        return await message.answer(_["errors"]["too_short"], parse_mode="html")

    await state.update_data(display_roll=message.text.strip())
    await message.answer(_["upload"]["ask_course"], reply_markup=course_kb(), parse_mode="html")
    await state.set_state(UploadState.waiting_for_course)


@app.callback_query(StateFilter(UploadState.waiting_for_course), lambda c: c.data.startswith("course_"))
async def upload_get_course(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)

    course_key = callback.data.split("_", 1)[1]
    await state.update_data(upload_course_key=course_key, display_course=course_key)

    await callback.message.edit_text(
        _["upload"]["ask_semester"], reply_markup=semester_kb(course_key), parse_mode="html"
    )
    await state.set_state(UploadState.waiting_for_semester)
    await callback.answer()


@app.callback_query(StateFilter(UploadState.waiting_for_semester), lambda c: c.data.startswith("sem_"))
async def upload_get_semester(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)

    sem_num = int(callback.data.split("_")[1])
    await state.update_data(display_semester=str(sem_num))

    data = await state.get_data()
    course_key = data.get("upload_course_key", "BTECH")

    if needs_department(course_key):
        await callback.message.edit_text(
            _["upload"]["ask_department"], reply_markup=department_kb(course_key, sem_num), parse_mode="html"
        )
        await state.set_state(UploadState.waiting_for_department)
    else:
        await state.update_data(display_department=None)
        item_type = data.get("item_type", "notes")
        if item_type == "pyqs":
            await callback.message.edit_text(_["upload"]["ask_year"], parse_mode="html")
            await state.set_state(UploadState.waiting_for_year)
        else:
            await callback.message.edit_text(_["upload"]["ask_session"], parse_mode="html")
            await state.set_state(UploadState.waiting_for_session)

    await callback.answer()


@app.callback_query(StateFilter(UploadState.waiting_for_department), lambda c: c.data.startswith("dept_"))
async def upload_get_department(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)

    dept_key = callback.data.split("_", 1)[1]
    await state.update_data(display_department=dept_key)

    data = await state.get_data()
    item_type = data.get("item_type", "notes")
    if item_type == "pyqs":
        await callback.message.edit_text(_["upload"]["ask_year"], parse_mode="html")
        await state.set_state(UploadState.waiting_for_year)
    else:
        await callback.message.edit_text(_["upload"]["ask_session"], parse_mode="html")
        await state.set_state(UploadState.waiting_for_session)
    await callback.answer()





@app.message(StateFilter(UploadState.waiting_for_session))
async def upload_get_session(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    _ = get_langs(lang)

    if not message.text or len(message.text.strip()) < 3:
        return await message.answer(_["errors"]["too_short"], parse_mode="html")

    await state.update_data(display_session=message.text.strip())
    await message.answer(_["upload"]["ask_subject"], parse_mode="html")
    await state.set_state(UploadState.waiting_for_subject)


@app.message(StateFilter(UploadState.waiting_for_year))
async def upload_get_year(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    _ = get_langs(lang)

    if not message.text or len(message.text.strip()) < 3:
        return await message.answer(_["errors"]["too_short"], parse_mode="html")

    await state.update_data(display_year=message.text.strip())
    await message.answer(_["upload"]["ask_subject"], parse_mode="html")
    await state.set_state(UploadState.waiting_for_subject)


# ─── Subject (common for Flow A and B) ───────────────────────

@app.message(StateFilter(UploadState.waiting_for_subject))
async def upload_get_subject(message: Message, state: FSMContext):
    lang = await _lang(message.from_user.id)
    _ = get_langs(lang)

    if not message.text or len(message.text.strip()) < 3:
        return await message.answer(_["errors"]["too_short"], parse_mode="html")

    await state.update_data(subject=message.text.strip())
    data = await state.get_data()

    session_or_year = data.get("display_year") if data.get("item_type") == "pyqs" else data.get("display_session")

    await message.answer(
        _["upload"]["confirm"].format(
            name=data.get("display_name", "N/A"),
            roll_no=data.get("display_roll", "N/A"),
            course=data.get("display_course", "N/A"),
            department=data.get("display_department") or "N/A",
            semester=data.get("display_semester", "N/A"),
            session=session_or_year or "N/A",
            subject=data["subject"],
        ),
        reply_markup=confirm_kb(),
        parse_mode="html",
    )
    await state.set_state(UploadState.confirming)


# ─── Confirm / Cancel ────────────────────────────────────────
# On confirm: NO DB insert, NO storage upload.
# Only send to admin channel and store metadata in-memory.

@app.callback_query(StateFilter(UploadState.confirming), lambda c: c.data == "confirm")
async def upload_confirm(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)
    data = await state.get_data()
    
    print(data)  # DEBUG

    try:
        subject = data["subject"]
        display_semester = data.get("display_semester")
        
        if not display_semester:
            raise Exception("Semester missing")

        # 1. Generate submission ID and store metadata in-memory
        submission_id = str(uuid.uuid4())[:8]  # short UUID for callback_data
        submissions.save(submission_id, {
            "user_id": callback.from_user.id,
            "file_id": data["file_id"],
            "item_type": data.get("item_type", "notes"),
            "subject": subject,
            "display_name": data.get("display_name", ""),
            "display_course": data.get("display_course", ""),
            "display_department": data.get("display_department"),
            "display_semester": display_semester,
            "display_session": data.get("display_session", ""),
            "display_year": data.get("display_year", ""),
        })

        # 2. Send PDF to admin channel (NO storage, NO DB)
        
        session_or_year = data.get("display_year") if data.get("item_type") == "pyqs" else data.get("display_session")
        
        caption = _["admin"]["new_note"].format(
            name=data.get("display_name", "N/A"),
            course=data.get("display_course", "N/A"),
            department=data.get("display_department") or "N/A",
            semester=data.get("display_semester", "N/A"),
            session=session_or_year or "N/A",
            subject=subject,
        )
        if data.get("item_type") == "pyqs":
            caption = "📜 <b>[PYQ]</b>\n" + caption

        await bot.send_document(
            chat_id=config.ADMIN_CHANNEL_ID,
            document=data["file_id"],
            caption=caption,
            reply_markup=inline.approval_btn(submission_id),
            parse_mode="html",
        )

        # 3. Log the upload attempt for daily limits
        await db_service.add_upload_log(callback.from_user.id)

        # 4. Notify user
        await callback.message.edit_text(_["upload"]["submitted"], parse_mode="html")

    except Exception as e:
        log.exception("Submission failed")
        await callback.message.edit_text(_["upload"]["upload_error"], parse_mode="html")

    await state.clear()
    await callback.answer()


@app.callback_query(StateFilter(UploadState.confirming), lambda c: c.data == "cancel")
async def upload_cancel(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)

    await callback.message.edit_text(_["upload"]["cancelled"], parse_mode="html")
    await state.clear()
    await callback.answer()