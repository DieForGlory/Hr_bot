# bot/keyboards/reply.py
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.locales.texts import get_text

def get_structure_kb(structure: list[str]) -> ReplyKeyboardMarkup:
    # Названия подразделений намеренно не переводятся (см. ограничение по оргструктуре)
    builder = ReplyKeyboardBuilder()
    for item in structure:
        builder.button(text=item)
    builder.adjust(1) # По одной кнопке в ряд для удобного чтения длинных названий
    return builder.as_markup(resize_keyboard=True)

def get_role_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=get_text("role_employee", lang))
    builder.button(text=get_text("role_manager", lang))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)