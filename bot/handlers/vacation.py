from datetime import datetime
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram3_calendar import SimpleCalendar, simple_cal_callback
from bot.utils.db_api import get_user_by_telegram_id, create_request
from bot.handlers.main_menu import get_main_keyboard

router = Router()


class VacationState(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_end_date = State()


@router.message(F.text == "📄 Отпуск")
async def vacation_menu(message: types.Message):
    # Убрано использование ReplyKeyboardMarkup для типов отпуска,
    # заменено на Inline для согласованности потока
    from bot.keyboards.inline import get_vacation_types_kb
    await message.answer("Выберите тип отпуска:", reply_markup=get_vacation_types_kb())


@router.callback_query(F.data.startswith("vac_type_"))
async def start_vacation_request(callback: CallbackQuery, state: FSMContext):
    vac_type = callback.data.split("_")[2]
    user = await get_user_by_telegram_id(callback.from_user.id)

    if vac_type == "paid" and user.vacation_days_balance <= 0:
        await callback.message.answer("У вас нет доступных дней для оплачиваемого отпуска.")
        await callback.answer()
        return

    await state.update_data(vacation_type=vac_type, balance=user.vacation_days_balance)
    await callback.message.answer(
        "Выберите дату начала отпуска:",
        reply_markup=await SimpleCalendar().start_calendar()
    )
    await state.set_state(VacationState.waiting_for_start_date)
    await callback.answer()


@router.callback_query(SimpleCalendar.filter(), VacationState.waiting_for_start_date)
async def process_start_date(callback: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback, callback_data)
    if selected:
        await state.update_data(start_date=date)
        await callback.message.answer(
            "Выберите дату окончания отпуска:",
            reply_markup=await SimpleCalendar().start_calendar()
        )
        await state.set_state(VacationState.waiting_for_end_date)


@router.callback_query(SimpleCalendar.filter(), VacationState.waiting_for_end_date)
async def process_end_date(callback: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, end_date = await SimpleCalendar().process_selection(callback, callback_data)
    if selected:
        data = await state.update_data(end_date=end_date)
        start_date = data['start_date']

        days_count = (end_date - start_date).days + 1
        if days_count <= 0:
            await callback.message.answer("Дата окончания должна быть позже даты начала.")
            return

        if data['vacation_type'] == 'paid' and days_count > data['balance']:
            await callback.message.answer(f"Запрошено {days_count} дней. Доступно только {data['balance']}.")
            return

        from bot.keyboards.inline import get_confirm_kb
        await callback.message.answer(
            f"Подтверждение:\nПериод: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}\n"
            f"Количество дней: {days_count}",
            reply_markup=get_confirm_kb()
        )


@router.callback_query(F.data == "confirm_vacation")
async def confirm_vacation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await get_user_by_telegram_id(callback.from_user.id)

    req_id = await create_request(
        user_id=user.id,
        req_type=f"vacation_{data['vacation_type']}",
        start_date=data['start_date'],
        end_date=data['end_date']
    )

    # Маршрутизация уведомления руководителю
    from bot.utils.routing import notify_manager
    await notify_manager(callback.bot, user, req_id, data)

    await callback.message.answer("Ваша заявка принята и направлена на согласование.", reply_markup=get_main_keyboard())
    await state.clear()