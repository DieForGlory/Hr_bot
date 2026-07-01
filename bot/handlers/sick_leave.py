# bot/handlers/sick_leave.py
import asyncio
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram3_calendar import SimpleCalendar, simple_cal_callback
from bot.utils.db_api import get_user_by_telegram_id, create_request
from bot.utils.scheduler import schedule_sick_leave_reminder

router = Router()


class SickLeaveState(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_document = State()


@router.message(F.text == "🏥 Больничный")
async def start_sick_leave(message: types.Message, state: FSMContext):
    await message.answer(
        "Выберите дату начала больничного:",
        reply_markup=await SimpleCalendar().start_calendar()
    )
    await state.set_state(SickLeaveState.waiting_for_start_date)


@router.callback_query(F.data.startswith("calendar_"), SickLeaveState.waiting_for_start_date)
async def process_start_date(callback: types.CallbackQuery, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback, callback.data)
    if selected:
        user = await get_user_by_telegram_id(callback.from_user.id)
        if user:
            await create_request(user.id, "sick_leave", start_date=date)

        await callback.message.answer("После завершения больничного не забудьте прикрепить подтверждающий документ.")
        await state.set_state(SickLeaveState.waiting_for_document)

        asyncio.create_task(schedule_sick_leave_reminder(callback.bot, callback.message.chat.id))