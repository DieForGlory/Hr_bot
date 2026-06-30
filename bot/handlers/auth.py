
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from bot.utils.db_api import get_user_by_telegram_id, get_user_by_phone, update_user_telegram_id
from bot.handlers.main_menu import get_main_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if user:
        await message.answer("Главное меню", reply_markup=get_main_keyboard())
    else:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отправить номер телефона", request_contact=True)]],
            resize_keyboard=True
        )
        await message.answer("Требуется авторизация. Отправьте номер телефона.", reply_markup=kb)

@router.message(F.contact)
async def process_contact(message: types.Message):
    phone = message.contact.phone_number.replace("+", "")
    user = await get_user_by_phone(phone)
    if user:
        await update_user_telegram_id(user.id, message.from_user.id)
        await message.answer("Авторизация успешна.", reply_markup=get_main_keyboard())
    else:
        await message.answer("Сотрудник с таким номером не найден в базе. Обратитесь в HR.", reply_markup=ReplyKeyboardRemove())