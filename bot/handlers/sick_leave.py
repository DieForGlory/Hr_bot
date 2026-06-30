import asyncio
from datetime import datetime
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from bot.utils.db_api import get_user_by_telegram_id, create_request
from bot.utils.scheduler import schedule_sick_leave_reminder
from bot.handlers.main_menu import get_main_keyboard

router = Router()


class SickLeaveState(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_document = State()


@router.message(F.text == "Больничный")
async def start_sick_leave(message: types.Message, state: FSMContext):
    await message.answer("Укажите дату начала больничного (ГГГГ-ММ-ДД):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SickLeaveState.waiting_for_start_date)


@router.message(SickLeaveState.waiting_for_start_date)
async def process_sick_leave_start(message: types.Message, state: FSMContext):
    try:
        start_date = datetime.strptime(message.text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Неверный формат. Используйте ГГГГ-ММ-ДД.")
        return

    user = await get_user_by_telegram_id(message.from_user.id)
    if user:
        await create_request(user.id, "sick_leave", start_date=start_date)

    await message.answer("После завершения больничного не забудьте прикрепить подтверждающий документ.")
    await state.set_state(SickLeaveState.waiting_for_document)

    asyncio.create_task(schedule_sick_leave_reminder(message.bot, message.chat.id))

    await message.answer("Главное меню", reply_markup=get_main_keyboard())


@router.message(SickLeaveState.waiting_for_document, F.document | F.photo)
async def process_sick_leave_document(message: types.Message, state: FSMContext):
    await message.answer("Документ успешно загружен. Заявка обновлена.")
    await state.clear()