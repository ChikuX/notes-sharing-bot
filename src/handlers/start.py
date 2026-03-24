"""Start handler – /start command and help."""
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from src.keyboards import inline
from src.locales import get_langs
from src.services import db_service

app = Router()


async def _lang(telegram_id: int) -> str:
    """Helper: get user language."""
    return await db_service.get_user_language(telegram_id)


@app.message(Command("start"))
async def start_command(m: Message):
    lang = await _lang(m.from_user.id)
    _ = get_langs(lang)
    await m.reply(_["start"]["welcome"], reply_markup=inline.START_BUTTON, parse_mode="html")


@app.callback_query(lambda c: c.data == "help")
async def help_handler(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)
    await callback.message.answer(
        "📖 <b>How to use this bot:</b>\n\n"
        "1️⃣ Create your <b>Profile</b> first\n"
        "2️⃣ Click <b>Upload Notes</b> and send a PDF\n"
        "3️⃣ Your notes will be reviewed by admins\n"
        "4️⃣ You'll get notified once approved!\n\n"
        "Use /start to see the main menu.",
        parse_mode="html",
    )
    await callback.answer()


@app.callback_query(lambda c: c.data == "back_home")
async def back_home(callback: CallbackQuery):
    lang = await _lang(callback.from_user.id)
    _ = get_langs(lang)
    await callback.message.edit_text(
        _["start"]["welcome"],
        reply_markup=inline.START_BUTTON,
        parse_mode="html",
    )
    await callback.answer()