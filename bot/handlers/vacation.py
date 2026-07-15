from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram3_calendar import SimpleCalendar, simple_cal_callback
from bot.utils.db_api import get_user_by_telegram_id, create_request, calculate_actual_vacation_days
from bot.handlers.main_menu import get_main_keyboard
from bot.utils.validators import to_date, is_valid_vacation_start
from bot.utils.constants import VACATION_TYPES_REQUIRING_DOCS
from bot.locales.texts import get_text, get_text_variants
from core.logging_config import action_logger

router = Router()

# Короткие ключи типов отпуска (callback vac_type_<key>) -> нужен ли баланс / документы
VACATION_TYPE_KEYS = ("paid", "unpaid", "marriage", "childbirth")
DOC_REQUIRED_KEYS = ("marriage", "childbirth")


def _fmt_num(value) -> str:
    """Число без лишнего '.0' (12.5 -> '12.5', 21.0 -> '21')."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value)
    return str(int(f)) if f == int(f) else str(round(f, 2))


class VacationState(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_end_date = State()
    waiting_for_document = State()


@router.message(F.text.in_(get_text_variants("vacation")))
async def vacation_menu(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"

    # Актуальный остаток отпускных «в любой момент» (п.3), если задана дата приёма
    if user:
        from bot.utils.vacation_balance import balance_for_user
        bal = balance_for_user(user)
        if bal is not None:
            await message.answer(get_text("vacation_balance_detail", lang).format(
                work=_fmt_num(bal.remaining_work),
                cal=_fmt_num(bal.remaining_calendar),
                total=_fmt_num(bal.total_remaining),
                bonus=_fmt_num(bal.tenure_bonus),
            ))

    from bot.keyboards.inline import get_vacation_types_kb
    await message.answer(get_text("vacation_choose_type", lang), reply_markup=get_vacation_types_kb(lang))


@router.callback_query(F.data.startswith("vac_type_"))
async def start_vacation_request(callback: CallbackQuery, state: FSMContext):
    vac_type = callback.data.split("_")[2]
    if vac_type not in VACATION_TYPE_KEYS:
        await callback.answer()
        return

    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language

    available = user.vacation_days_balance
    if vac_type == "paid":
        # Остаток считаем по алгоритму Excel (п.3): списываемая корзина — календарная.
        from bot.utils.vacation_balance import balance_for_user
        bal = balance_for_user(user)
        if bal is not None:
            available = bal.remaining_calendar

        if available <= 0:
            await callback.message.answer(get_text("vacation_no_balance", lang))
            await callback.answer()
            return

        if bal is not None:
            await callback.message.answer(get_text("vacation_balance_detail", lang).format(
                work=_fmt_num(bal.remaining_work),
                cal=_fmt_num(bal.remaining_calendar),
                total=_fmt_num(bal.total_remaining),
                bonus=_fmt_num(bal.tenure_bonus),
            ))
        else:
            await callback.message.answer(get_text("vacation_balance_info", lang).format(balance=_fmt_num(available)))

    await state.update_data(vacation_type=vac_type, balance=available)
    await callback.message.answer(
        get_text("vacation_choose_start", lang),
        reply_markup=await SimpleCalendar().start_calendar()
    )
    await state.set_state(VacationState.waiting_for_start_date)
    await callback.answer()


@router.callback_query(simple_cal_callback.filter(), VacationState.waiting_for_start_date)
async def process_start_date(callback: CallbackQuery, callback_data: simple_cal_callback, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.language if user else "ru"
    selected, selected_date = await SimpleCalendar().process_selection(callback, callback_data)
    if not selected:
        return

    start_date = to_date(selected_date)
    if not is_valid_vacation_start(start_date):
        await callback.message.answer(
            get_text("vacation_start_in_past", lang),
            reply_markup=await SimpleCalendar().start_calendar()
        )
        return

    await state.update_data(start_date=start_date)
    await callback.message.answer(
        get_text("vacation_choose_end", lang),
        reply_markup=await SimpleCalendar().start_calendar()
    )
    await state.set_state(VacationState.waiting_for_end_date)


@router.callback_query(simple_cal_callback.filter(), VacationState.waiting_for_end_date)
async def process_end_date(callback: types.CallbackQuery, callback_data: simple_cal_callback, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.language if user else "ru"
    selected, selected_date = await SimpleCalendar().process_selection(callback, callback_data)
    if not selected:
        return

    end_date = to_date(selected_date)
    data = await state.get_data()
    start_date = data.get('start_date')
    if not start_date or not data.get('vacation_type'):
        await callback.message.answer(get_text("session_expired", lang))
        await state.clear()
        return

    if end_date < start_date:
        await callback.message.answer(
            get_text("vacation_end_before_start", lang),
            reply_markup=await SimpleCalendar().start_calendar()
        )
        return

    # Расчет дней с учетом производственного календаря
    actual_days = await calculate_actual_vacation_days(start_date, end_date)

    if actual_days <= 0:
        await callback.message.answer(
            get_text("vacation_only_holidays", lang),
            reply_markup=await SimpleCalendar().start_calendar()
        )
        return

    if data['vacation_type'] == 'paid' and actual_days > data['balance']:
        await callback.message.answer(
            get_text("vacation_over_balance", lang).format(days=actual_days, balance=data['balance']),
            reply_markup=await SimpleCalendar().start_calendar()
        )
        return

    await state.update_data(end_date=end_date, days_count=actual_days)

    from bot.keyboards.inline import get_confirm_kb
    await callback.message.answer(
        get_text("vacation_confirmation_summary", lang).format(
            start=start_date.strftime('%d.%m.%Y'), end=end_date.strftime('%d.%m.%Y'), days=actual_days
        ),
        reply_markup=get_confirm_kb(lang)
    )


@router.callback_query(F.data == "confirm_vacation")
async def confirm_vacation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.language if user else "ru"

    # Защита от повторного клика по кнопке после отправки заявки
    if not user or not data.get('start_date') or not data.get('end_date') or not data.get('vacation_type'):
        await callback.answer(get_text("session_expired", lang), show_alert=True)
        return

    # Спец. отпуска (п.4): перед отправкой на согласование запрашиваем документы.
    # Без загрузки документа заявка не создаётся и на согласование не уходит.
    if data['vacation_type'] in DOC_REQUIRED_KEYS:
        await callback.message.answer(get_text("vacation_doc_request", lang))
        await state.set_state(VacationState.waiting_for_document)
        await callback.answer()
        return

    req_id = await create_request(
        user_id=user.id,
        req_type=f"vacation_{data['vacation_type']}",
        start_date=data['start_date'],
        end_date=data['end_date'],
        days_count=data['days_count']
    )
    action_logger.info("request_created type=vacation_%s user_id=%s req_id=%s", data['vacation_type'], user.id, req_id)

    # Маршрутизация уведомления руководителю
    from bot.utils.routing import notify_manager
    await notify_manager(callback.bot, user, req_id, data)

    await callback.message.answer(get_text("vacation_submitted", lang), reply_markup=get_main_keyboard(lang))
    await state.clear()
    await callback.answer()


@router.message(VacationState.waiting_for_document, F.photo | F.document)
async def process_vacation_document(message: types.Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    data = await state.get_data()

    if not user or not data.get('start_date') or not data.get('end_date') or not data.get('vacation_type'):
        await message.answer(get_text("session_expired", lang))
        await state.clear()
        return

    file_id = message.document.file_id if message.document else message.photo[-1].file_id

    req_id = await create_request(
        user_id=user.id,
        req_type=f"vacation_{data['vacation_type']}",
        start_date=data['start_date'],
        end_date=data['end_date'],
        days_count=data['days_count'],
        file_path=file_id,
    )
    action_logger.info("request_created type=vacation_%s user_id=%s req_id=%s (with document)", data['vacation_type'], user.id, req_id)

    from bot.utils.routing import notify_manager
    await notify_manager(message.bot, user, req_id, data, document_file_id=file_id)

    await message.answer(get_text("vacation_doc_received", lang), reply_markup=get_main_keyboard(lang))
    await state.clear()


@router.message(VacationState.waiting_for_document)
async def process_vacation_document_invalid(message: types.Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(get_text("vacation_doc_invalid", lang))


@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.language if user else "ru"
    await state.clear()
    await callback.message.answer(get_text("back_to_menu", lang), reply_markup=get_main_keyboard(lang))
    await callback.answer()
