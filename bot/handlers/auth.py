from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram3_calendar import DialogCalendar, dialog_cal_callback

from bot.utils.db_api import get_user_by_telegram_id, get_user_by_phone, update_user_telegram_id, create_pending_user
from bot.handlers.main_menu import get_main_keyboard
from bot.utils.constants import COMPANY_STRUCTURE
from bot.utils.validators import is_valid_full_name, is_valid_birth_date, to_date, clean_text, MAX_CAR_INFO_LEN
from bot.keyboards.reply import get_structure_kb, get_role_kb
from bot.utils.routing import send_registration_to_hr
from bot.locales.texts import get_text
from core.logging_config import action_logger

router = Router()

# Стартовый год календаря даты рождения (середина типичного диапазона сотрудников)
BIRTH_CALENDAR_START_YEAR = 1995


class RegistrationState(StatesGroup):
    full_name = State()
    subdivision = State()
    role_flag = State()
    birth_date = State()
    car_info = State()
    photo = State()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if user:
        if user.approval_status == "pending":
            await message.answer("Анкета находится на рассмотрении HR.")
        elif user.approval_status == "rejected":
            await message.answer("В регистрации отказано. Обратитесь в отдел кадров.")
        else:
            await message.answer("Главное меню", reply_markup=get_main_keyboard(user.language))
    else:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отправить номер телефона", request_contact=True)]],
            resize_keyboard=True
        )
        await message.answer("Система HR. Требуется идентификация по номеру телефона.", reply_markup=kb)


@router.message(F.contact)
async def process_contact(message: types.Message, state: FSMContext):
    # Принимаем только собственный контакт пользователя, а не пересланный чужой
    if not message.contact.user_id or message.contact.user_id != message.from_user.id:
        await message.answer(get_text("contact_not_yours", "ru"))
        return

    phone = message.contact.phone_number.replace("+", "")
    user = await get_user_by_phone(phone)

    if user:
        await update_user_telegram_id(user.id, message.from_user.id)
        action_logger.info("user_identified user_id=%s", user.id)
        await message.answer("Идентификация успешна.", reply_markup=get_main_keyboard(user.language))
    else:
        await state.update_data(
            phone=phone,
            telegram_id=message.from_user.id,
            tg_username=message.from_user.username
        )
        await message.answer(
            "Сотрудник не найден в базе. Начат процесс регистрации.\n\nВведите ФИО (по паспорту на латинице):",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(RegistrationState.full_name)


@router.message(RegistrationState.full_name, F.text)
async def process_full_name(message: types.Message, state: FSMContext):
    full_name = message.text.strip()
    if not is_valid_full_name(full_name):
        await message.answer(get_text("invalid_full_name", "ru"))
        return

    await state.update_data(full_name=full_name)
    await message.answer(
        "Выберите ваше подразделение из списка:",
        reply_markup=get_structure_kb(COMPANY_STRUCTURE)
    )
    await state.set_state(RegistrationState.subdivision)


@router.message(RegistrationState.full_name)
async def process_full_name_invalid(message: types.Message):
    await message.answer(get_text("only_text_allowed", "ru"))


@router.message(RegistrationState.subdivision, F.text.in_(COMPANY_STRUCTURE))
async def process_subdivision(message: types.Message, state: FSMContext):
    await state.update_data(subdivision=message.text)
    await message.answer("Укажите ваш статус:", reply_markup=get_role_kb())
    await state.set_state(RegistrationState.role_flag)


@router.message(RegistrationState.subdivision)
async def process_subdivision_invalid(message: types.Message):
    await message.answer(get_text("choose_from_list", "ru"))


@router.message(RegistrationState.role_flag, F.text.in_(["Сотрудник", "Руководитель"]))
async def process_role_flag(message: types.Message, state: FSMContext):
    await state.update_data(role_text=message.text)
    await message.answer(
        get_text("birth_choose", "ru"),
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "Сначала выберите год:",
        reply_markup=await DialogCalendar.start_calendar(year=BIRTH_CALENDAR_START_YEAR)
    )
    await state.set_state(RegistrationState.birth_date)


@router.message(RegistrationState.role_flag)
async def process_role_flag_invalid(message: types.Message):
    await message.answer(get_text("choose_from_list", "ru"))


@router.callback_query(dialog_cal_callback.filter(), RegistrationState.birth_date)
async def process_birth_date(callback: types.CallbackQuery, callback_data: dialog_cal_callback, state: FSMContext):
    selected, selected_date = await DialogCalendar().process_selection(callback, callback_data)
    if not selected:
        return

    birth_date = to_date(selected_date)
    if not is_valid_birth_date(birth_date):
        await callback.message.answer(get_text("invalid_birth_date", "ru"))
        await callback.message.answer(
            "Сначала выберите год:",
            reply_markup=await DialogCalendar.start_calendar(year=BIRTH_CALENDAR_START_YEAR)
        )
        return

    await state.update_data(birth_date=birth_date.strftime("%d.%m.%Y"))
    await callback.message.answer("Укажите номер и марку автомобиля (или отправьте '-' если нет):")
    await state.set_state(RegistrationState.car_info)


@router.message(RegistrationState.birth_date)
async def process_birth_date_invalid(message: types.Message):
    await message.answer(get_text("use_calendar", "ru"))


@router.message(RegistrationState.car_info, F.text)
async def process_car_info(message: types.Message, state: FSMContext):
    car_info = clean_text(message.text, MAX_CAR_INFO_LEN)
    if car_info is None:
        await message.answer(get_text("car_info_invalid", "ru"))
        return

    await state.update_data(car_info=car_info)
    await message.answer("Загрузите фото для Face ID:")
    await state.set_state(RegistrationState.photo)


@router.message(RegistrationState.car_info)
async def process_car_info_invalid(message: types.Message):
    await message.answer(get_text("car_info_invalid", "ru"))


@router.message(RegistrationState.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.update_data(face_id_photo=photo_id)

    user_id = await create_pending_user(data)
    await send_registration_to_hr(message.bot, user_id, data)
    action_logger.info("registration_submitted user_id=%s", user_id)

    await message.answer("Анкета отправлена в HR. Ожидайте уведомления о результатах проверки.")
    await state.clear()


@router.message(RegistrationState.photo)
async def process_photo_invalid(message: types.Message):
    await message.answer(get_text("photo_required", "ru"))
