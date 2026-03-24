"""Settings handler – language selection."""
from aiogram import Router
from aiogram.types import CallbackQuery

from src.keyboards import inline
from src.locales import get_langs
from src.services import db_service

app = Router()

LANG_NAMES = {"en": "English", "hi": "हिंदी", "pu": "ਪੰਜਾਬੀ"}


@app.callback_query(lambda c: c.data == "language")
async def language_handler(callback: CallbackQuery):
    lang = await db_service.get_user_language(callback.from_user.id)
    _ = get_langs(lang)

    await callback.message.edit_text(
        _["settings"]["choose_language"],
        reply_markup=inline.language_kb(),
        parse_mode="html",
    )
    await callback.answer()


@app.callback_query(lambda c: c.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    new_lang = callback.data.split("_")[1]

    await db_service.update_user_language(callback.from_user.id, new_lang)

    _ = get_langs(new_lang)
    lang_display = LANG_NAMES.get(new_lang, new_lang)

    await callback.message.edit_text(
        _["settings"]["language_set"].format(lang=lang_display),
        parse_mode="html",
    )
    await callback.answer()