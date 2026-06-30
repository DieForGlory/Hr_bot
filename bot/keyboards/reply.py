# bot/keyboards/reply.py
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_structure_kb(structure: list[str]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for item in structure:
        builder.button(text=item)
    builder.adjust(1) # По одной кнопке в ряд для удобного чтения длинных названий
    return builder.as_markup(resize_keyboard=True)

def get_role_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Сотрудник")
    builder.button(text="Руководитель")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)