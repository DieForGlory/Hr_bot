# bot/handlers/sick_leave.py
from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram3_calendar import SimpleCalendar, simple_cal_callback
from bot.utils.db_api import (
    get_user_by_telegram_id, create_request, attach_sick_leave_document,
    get_users_by_role, get_open_sick_leave_request,
)
from bot.utils.scheduler import schedule_sick_leave_reminder
from bot.utils.validators import to_date, is_valid_sick_leave_start
from bot.locales.texts import get_text
from core.logging_config import action_logger

router = Router()


class SickLeaveState(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_document = State()


@router.message(F.text == "🏥 Больничный")
async def start_sick_leave(message: types.Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(
        get_text("sick_choose_start", lang),
        reply_markup=await SimpleCalendar().start_calendar()
    )
    await state.set_state(SickLeaveState.waiting_for_start_date)


@router.callback_query(simple_cal_callback.filter(), SickLeaveState.waiting_for_start_date)
async def process_start_date(callback: types.CallbackQuery, callback_data: simple_cal_callback, state: FSMContext):
    selected, selected_date = await SimpleCalendar().process_selection(callback, callback_data)
    if not selected:
        return

    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language

    start_date = to_date(selected_date)
    if not is_valid_sick_leave_start(start_date):
        await callback.message.answer(
            get_text("sick_date_out_of_range", lang),
            reply_markup=await SimpleCalendar().start_calendar()
        )
        return

    req_id = await create_request(user.id, "sick_leave", start_date=start_date)
    action_logger.info("request_created type=sick_leave user_id=%s req_id=%s", user.id, req_id)

    await state.update_data(request_id=req_id)
    await callback.message.answer(get_text("sick_attach_reminder", lang))
    await state.set_state(SickLeaveState.waiting_for_document)

    schedule_sick_leave_reminder(callback.bot, user.telegram_id)


async def _attach_and_forward(message: types.Message, user, req_id: int, lang: str):
    file_id = message.document.file_id if message.document else message.photo[-1].file_id

    await attach_sick_leave_document(req_id, file_id)
    action_logger.info("sick_leave_document_attached user_id=%s req_id=%s", user.id, req_id)

    hr_users = await get_users_by_role("hr")
    caption = f"Подтверждающий документ по больничному от {user.full_name}"
    for hr in hr_users:
        if hr.telegram_id:
            if message.document:
                await message.bot.send_document(hr.telegram_id, message.document.file_id, caption=caption)
            else:
                await message.bot.send_photo(hr.telegram_id, message.photo[-1].file_id, caption=caption)

    await message.answer(get_text("sick_document_received", lang))


@router.message(SickLeaveState.waiting_for_document, F.photo | F.document)
async def process_document(message: types.Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        return
    lang = user.language
    data = await state.get_data()
    req_id = data.get("request_id")

    if not req_id:
        open_req = await get_open_sick_leave_request(user.id)
        req_id = open_req.id if open_req else None

    if req_id:
        await _attach_and_forward(message, user, req_id, lang)
    await state.clear()


@router.message(SickLeaveState.waiting_for_document)
async def process_document_fallback(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(get_text("sick_waiting_document", lang))


@router.message(StateFilter(None), F.photo | F.document)
async def process_late_document(message: types.Message):
    """Сотрудник прикрепляет документ после завершения больничного,
    когда диалоговое состояние уже потеряно (например, после напоминания через 3 дня)."""
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        return

    open_req = await get_open_sick_leave_request(user.id)
    if not open_req:
        return

    await _attach_and_forward(message, user, open_req.id, user.language)
