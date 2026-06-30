from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.utils.db_api import get_user_by_telegram_id, get_user_requests

router = Router()


def get_main_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Отпуск")
    builder.button(text="Справки")
    builder.button(text="Больничный")
    builder.button(text="FAQ")
    builder.button(text="Мои заявки")
    builder.button(text="Полезные контакты")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Главное меню", reply_markup=get_main_keyboard())


@router.message(F.text == "FAQ")
async def faq_menu(message: types.Message):
    await message.answer(
        "В какие даты выплачивается аванс и заработная плата?\n"
        "Как рассчитываются отпускные?\n"
        "Как рассчитывается аванс и заработная плата?\n"
        "Как рассчитываются больничные?\n"
        "Как рассчитываются декретные?\n"
        "Сколько отпускных дней положено работнику?\n"
        "Где скачать персональные документы?\n"
        "Где проверить стаж работы?\n"
        "Кто может восстановить стаж работы?\n"
        "Где скачать больничный лист?"
    )


@router.message(F.text == "Мои заявки")
async def my_requests(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Пользователь не найден в базе.")
        return

    reqs = await get_user_requests(user.id)
    if not reqs:
        await message.answer("Список ваших заявок пуст.")
        return

    text = "Ваши заявки:\n\n"
    for r in reqs:
        text += f"Тип: {r.type} | Статус: {r.status} | Даты: {r.start_date} - {r.end_date}\n"
    await message.answer(text)


@router.message(F.text == "Полезные контакты")
async def contacts_menu(message: types.Message):
    await message.answer("Контакты.")