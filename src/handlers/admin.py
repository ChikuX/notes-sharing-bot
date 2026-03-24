"""
Admin handler – approve / reject notes from admin channel.

On APPROVE:
  1. Look up submission from in-memory store
  2. Download file from Telegram (file_id)
  3. Upload to Supabase Storage
  4. Insert record into Neon DB (status=approved, file_url set)
  5. Notify user

On REJECT:
  1. Insert record into Neon DB (status=rejected, file_url=NULL)
  2. Notify user
  3. NO storage upload
"""
import logging
from aiogram import Router
from aiogram.types import CallbackQuery

from src.locales import get_langs
from src.services import db_service, storage_service, submissions
from src.core.bot import bot
from src.core.config import config
from src.keyboards.inline import ACADEMIC_STRUCTURE, get_valid_departments

app = Router()
log = logging.getLogger(__name__)


@app.callback_query(lambda c: c.data.startswith(("approve_", "reject_")))
async def handle_admin_action(callback: CallbackQuery):
    admin_id = callback.from_user.id

    # Authorization check
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("🚫 Not authorized", show_alert=True)
        return

    parts = callback.data.split("_", 1)
    action = parts[0]             # "approve" or "reject"
    submission_id = parts[1]      # short UUID

    # Look up submission from in-memory store
    sub = submissions.get(submission_id)
    if not sub:
        await callback.answer("⚠️ Submission expired or already processed", show_alert=True)
        return

    user_id = sub["user_id"]
    file_id = sub["file_id"]
    subject = sub["subject"]
    lang = await db_service.get_user_language(user_id)
    _ = get_langs(lang)

    if action == "approve":
        await callback.answer("⏳ Uploading to storage...")

        try:
            # 1. Download file from Telegram using file_id
            file = await bot.get_file(file_id)
            file_bytes_io = await bot.download_file(file.file_path)
            file_bytes = file_bytes_io.read()

            # 2. Upload to Supabase Storage bucket
            course = sub.get("display_course") or "unknown"
            file_name = storage_service.build_file_name(course, subject)
            file_url = await storage_service.upload_pdf(file_bytes, file_name)

            # 3. Validate and Print Final Data
            display_semester = sub.get("display_semester")
            if not display_semester:
                raise Exception("Semester missing")

            print("FINAL DATA:", {
                "type": sub.get("item_type", "notes"),
                "name": sub.get("display_name", ""),
                "course": sub.get("display_course", ""),
                "dept": sub.get("display_department"),
                "semester": display_semester,
                "session_or_year": sub.get("display_year") if sub.get("item_type") == "pyqs" else sub.get("display_session", "")
            })

            # Strict Academic Validation
            course_val = sub.get("display_course", "").upper()
            if course_val not in ACADEMIC_STRUCTURE:
                raise Exception(f"Invalid course: {course_val}")

            sem_val = int(display_semester)
            if sem_val > ACADEMIC_STRUCTURE[course_val]["semesters"]:
                raise Exception(f"Invalid semester: {sem_val}")

            valid_depts = get_valid_departments(course_val, sem_val)
            dept_val = sub.get("display_department")
            
            if valid_depts is not None:
                if dept_val not in valid_depts:
                    raise Exception(f"Invalid department '{dept_val}' for course {course_val} semester {sem_val}")
            else:
                if dept_val:
                    # Clean up random departments passed when none are expected
                    dept_val = None

            item_type = sub.get("item_type", "notes")
            if item_type == "pyqs":
                year_val = sub.get("display_year")
                if not year_val:
                    raise Exception("Year missing for PYQ")
                
                await db_service.insert_pyq(
                    file_url=file_url,
                    subject=subject,
                    display_name=sub.get("display_name", ""),
                    display_course=sub.get("display_course", ""),
                    display_department=dept_val,
                    display_semester=str(sem_val),
                    year=year_val,
                    status="approved",
                )
            else:
                await db_service.insert_note(
                    uploaded_by=user_id,
                    file_id=file_id,
                    file_url=file_url,
                    subject=subject,
                    display_name=sub.get("display_name", ""),
                    display_course=sub.get("display_course", ""),
                    display_department=dept_val,
                    display_semester=str(sem_val),
                    display_session=sub.get("display_session", ""),
                    status="approved",
                )

            # 4. Notify uploader
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=_["admin"]["approved"].format(subject=subject),
                    parse_mode="html",
                )
            except Exception as e:
                log.warning(f"Could not notify user {user_id}: {e}")

            # 5. Update admin channel message
            await callback.message.edit_caption(
                caption=callback.message.caption + "\n\n✅ <b>APPROVED</b>",
                parse_mode="html",
            )

            # 6. Remove from pending store (prevent duplicate approval)
            submissions.remove(submission_id)

        except Exception as e:
            log.exception(f"Approval failed for submission {submission_id}")
            await callback.answer("❌ Upload to storage failed!", show_alert=True)
            return

    elif action == "reject":
        # REJECT: NO DB insert, NO storage upload. Pure notification only.

        # 1. Notify uploader
        try:
            await bot.send_message(
                chat_id=user_id,
                text=_["admin"]["rejected"].format(subject=subject),
                parse_mode="html",
            )
        except Exception as e:
            log.warning(f"Could not notify user {user_id}: {e}")

        # 2. Update admin channel message
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n❌ <b>REJECTED</b>",
            parse_mode="html",
        )

        # 3. Remove from pending store
        submissions.remove(submission_id)

        await callback.answer("❌ Rejected")
