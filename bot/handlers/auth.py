from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram3_calendar import DialogCalendar, dialog_cal_callback

from bot.utils.db_api import get_user_by_telegram_id, get_user_by_phone, update_user_telegram_id, create_pending_user
from bot.handlers.main_menu import get_main_keyboard
from bot.utils.constants import COMPANY_STRUCTURE
from bot.utils.validators import is_valid_full_name, is_valid_birth_date, to_date, clean_text, MAX_CAR_INFO_LEN
from bot.keyboards.reply import get_structure_kb, get_role_kb
from bot.utils.routing import send_registration_to_hr
from bot.locales.texts import get_text, get_text_variants, resolve_choice
from core.logging_config import action_logger

router = Router()

# Стартовый год календаря даты рождения (середина типичного диапазона сотрудников)
BIRTH_CALENDAR_START_YEAR = 1995

ROLE_CHOICES = {"employee": "role_employee", "manager": "role_manager"}


class RegistrationState(StatesGroup):
    full_name = State()
    subdivision = State()
    role_flag = State()
    birth_date = State()
    car_info = State()
    photo = State()


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if user:
        if user.approval_status == "pending":
            await message.answer(get_text("registration_pending", user.language))
        elif user.approval_status == "rejected":
            await message.answer(get_text("registration_rejected_msg", user.language))
        else:
            await message.answer(get_text("back_to_menu", user.language), reply_markup=get_main_keyboard(user.language))
        return

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="reglang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="reglang_uz")]
    ])
    await message.answer(get_text("choose_language", "ru"), reply_markup=kb)


@router.callback_query(F.data.startswith("reglang_"))
async def process_registration_language(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    if lang not in ("ru", "uz"):
        await callback.answer()
        return

    await state.update_data(chosen_language=lang)

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_text("send_phone_button", lang), request_contact=True)]],
        resize_keyboard=True
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(get_text("send_phone_prompt", lang), reply_markup=kb)
    await callback.answer()


@router.message(F.contact)
async def process_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("chosen_language", "ru")

    # Принимаем только собственный контакт пользователя, а не пересланный чужой
    if not message.contact.user_id or message.contact.user_id != message.from_user.id:
        await message.answer(get_text("contact_not_yours", lang))
        return

    phone = message.contact.phone_number.replace("+", "")
    user = await get_user_by_phone(phone)

    if user:
        await update_user_telegram_id(user.id, message.from_user.id)
        action_logger.info("user_identified user_id=%s", user.id)
        await message.answer(get_text("identification_success", user.language), reply_markup=get_main_keyboard(user.language))
        await state.clear()
    else:
        await state.update_data(
            phone=phone,
            telegram_id=message.from_user.id,
            tg_username=message.from_user.username,
            chosen_language=lang,
        )
        await message.answer(
            get_text("registration_start_prompt", lang),
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(RegistrationState.full_name)


@router.message(RegistrationState.full_name, F.text)
async def process_full_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("chosen_language", "ru")

    full_name = message.text.strip()
    if not is_valid_full_name(full_name):
        await message.answer(get_text("invalid_full_name", lang))
        return

    await state.update_data(full_name=full_name)
    await message.answer(
        get_text("department_choose", lang),
        reply_markup=get_structure_kb(COMPANY_STRUCTURE)
    )
    await state.set_state(RegistrationState.subdivision)


@router.message(RegistrationState.full_name)
async def process_full_name_invalid(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    await message.answer(get_text("only_text_allowed", lang))


@router.message(RegistrationState.subdivision, F.text.in_(COMPANY_STRUCTURE))
async def process_subdivision(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("chosen_language", "ru")

    await state.update_data(subdivision=message.text)
    await message.answer(get_text("status_choose", lang), reply_markup=get_role_kb(lang))
    await state.set_state(RegistrationState.role_flag)


@router.message(RegistrationState.subdivision)
async def process_subdivision_invalid(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    await message.answer(get_text("choose_from_list", lang))


@router.message(
    RegistrationState.role_flag,
    F.text.in_(get_text_variants("role_employee") + get_text_variants("role_manager"))
)
async def process_role_flag(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("chosen_language", "ru")

    canonical_role = resolve_choice(ROLE_CHOICES, message.text)
    # В БД всегда сохраняем канонический русский вариант (HR читает в админке
    # и в уведомлении о регистрации), независимо от языка, на котором шла анкета
    role_text_ru = get_text(ROLE_CHOICES[canonical_role], "ru")
    await state.update_data(role_text=role_text_ru)

    await message.answer(
        get_text("birth_choose", lang),
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        get_text("birth_pick_year", lang),
        reply_markup=await DialogCalendar.start_calendar(year=BIRTH_CALENDAR_START_YEAR)
    )
    await state.set_state(RegistrationState.birth_date)


@router.message(RegistrationState.role_flag)
async def process_role_flag_invalid(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    await message.answer(get_text("choose_from_list", lang))


@router.callback_query(dialog_cal_callback.filter(), RegistrationState.birth_date)
async def process_birth_date(callback: types.CallbackQuery, callback_data: dialog_cal_callback, state: FSMContext):
    data = await state.get_data()
    lang = data.get("chosen_language", "ru")

    selected, selected_date = await DialogCalendar().process_selection(callback, callback_data)
    if not selected:
        return

    birth_date = to_date(selected_date)
    if not is_valid_birth_date(birth_date):
        await callback.message.answer(get_text("invalid_birth_date", lang))
        await callback.message.answer(
            get_text("birth_pick_year", lang),
            reply_markup=await DialogCalendar.start_calendar(year=BIRTH_CALENDAR_START_YEAR)
        )
        return

    await state.update_data(birth_date=birth_date.strftime("%d.%m.%Y"))
    await callback.message.answer(get_text("car_info_prompt", lang))
    await state.set_state(RegistrationState.car_info)


@router.message(RegistrationState.birth_date)
async def process_birth_date_invalid(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    await message.answer(get_text("use_calendar", lang))


@router.message(RegistrationState.car_info, F.text)
async def process_car_info(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("chosen_language", "ru")

    car_info = clean_text(message.text, MAX_CAR_INFO_LEN)
    if car_info is None:
        await message.answer(get_text("car_info_invalid", lang))
        return

    await state.update_data(car_info=car_info)
    await message.answer(get_text("photo_prompt", lang))
    await state.set_state(RegistrationState.photo)


@router.message(RegistrationState.car_info)
async def process_car_info_invalid(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    await message.answer(get_text("car_info_invalid", lang))


@router.message(RegistrationState.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.update_data(face_id_photo=photo_id)
    lang = data.get("chosen_language", "ru")

    data["language"] = lang
    user_id = await create_pending_user(data)
    await send_registration_to_hr(message.bot, user_id, data)
    action_logger.info("registration_submitted user_id=%s", user_id)

    await message.answer(get_text("registration_submitted", lang))
    await state.clear()


@router.message(RegistrationState.photo)
async def process_photo_invalid(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    await message.answer(get_text("photo_required", lang))
