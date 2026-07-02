from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.db_api import get_user_by_telegram_id
from bot.locales.texts import get_text
from sqlalchemy import update
from db.database import async_session
from db.models import User
from aiogram.filters import Command
from core.logging_config import action_logger

router = Router()


@router.message(Command("language"))
async def cmd_language(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz")]
    ])
    await message.answer(get_text("choose_language", "ru"), reply_markup=kb)


@router.callback_query(F.data.startswith("lang_"))
async def process_language_change(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user = await get_user_by_telegram_id(callback.from_user.id)

    async with async_session() as session:
        await session.execute(update(User).where(User.id == user.id).values(language=lang))
        await session.commit()

    action_logger.info("language_changed user_id=%s lang=%s", user.id, lang)
    await callback.message.edit_text(get_text("lang_saved", lang))

    from bot.handlers.main_menu import get_main_keyboard
    await callback.message.answer(get_text("main_menu", lang), reply_markup=get_main_keyboard(lang))
    await callback.answer()