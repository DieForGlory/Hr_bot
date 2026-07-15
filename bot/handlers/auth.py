from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram3_calendar import DialogCalendar, dialog_cal_callback

from bot.utils.db_api import (
    get_user_by_telegram_id, get_user_by_phone, update_user_telegram_id, create_pending_user,
    get_directory_users_by_department, get_user_by_id, claim_directory_user,
)
from bot.handlers.main_menu import get_main_keyboard
from bot.utils.constants import COMPANY_STRUCTURE
from bot.utils.org_hierarchy import get_children, get_parent_department, get_department_path, display_name
from bot.utils.validators import is_valid_full_name, is_valid_birth_date, to_date, clean_text, MAX_CAR_INFO_LEN
from bot.keyboards.reply import get_role_kb
from bot.keyboards.inline import get_org_nav_kb, get_reg_self_confirm_kb
from bot.utils.routing import send_registration_to_hr
from bot.locales.texts import get_text, get_text_variants, resolve_choice
from core.logging_config import action_logger

router = Router()

# Стартовый год календаря даты рождения (середина типичного диапазона сотрудников)
BIRTH_CALENDAR_START_YEAR = 1995

ROLE_CHOICES = {"employee": "role_employee", "manager": "role_manager"}


class RegistrationState(StatesGroup):
    navigating = State()        # навигация по оргструктуре / выбор себя (п.7/8)
    confirm_self = State()      # подтверждение выбранной записи справочника
    manual_full_name = State()  # ручная регистрация («Меня нет в списке»)
    manual_role = State()
    manual_birth = State()
    car_info = State()          # общий шаг (claim + manual)
    photo = State()             # общий шаг (claim + manual)


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

    # Идентификация по номеру — только для «настоящих» записей (не справочных заготовок)
    if user and user.approval_status != "directory":
        await update_user_telegram_id(user.id, message.from_user.id)
        action_logger.info("user_identified user_id=%s", user.id)
        await message.answer(get_text("identification_success", user.language), reply_markup=get_main_keyboard(user.language))
        await state.clear()
        return

    # Регистрация через справочник (п.7/8): пользователь ищет себя в оргструктуре.
    await state.update_data(
        phone=phone,
        telegram_id=message.from_user.id,
        tg_username=message.from_user.username,
        chosen_language=lang,
        current_dept=None,
        claimed_user_id=None,
    )
    await message.answer(get_text("reg_choose_department_hint", lang), reply_markup=ReplyKeyboardRemove())
    text, kb = await _nav_view(state, lang)
    await message.answer(text, reply_markup=kb)
    await state.set_state(RegistrationState.navigating)


# --- Навигация по оргструктуре / выбор себя из справочника --------------------

async def _nav_view(state: FSMContext, lang: str):
    """Собирает текст-заголовок и inline-клавиатуру для текущего узла оргструктуры."""
    data = await state.get_data()
    current = data.get("current_dept")
    children = get_children(current)
    employees = await get_directory_users_by_department(current) if current else []

    if current:
        breadcrumb = " › ".join(display_name(x) for x in get_department_path(current))
        if not children and not employees:
            header = f"📍 {breadcrumb}\n\n{get_text('reg_dept_no_employees', lang)}"
        else:
            header = f"📍 {breadcrumb}"
    else:
        header = get_text("reg_choose_top", lang)

    kb = get_org_nav_kb(current, children, employees, lang)
    return header, kb


async def _safe_edit(callback: types.CallbackQuery, text: str, kb):
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        try:
            await callback.message.edit_reply_markup(reply_markup=kb)
        except Exception:
            pass


@router.callback_query(RegistrationState.navigating, F.data.startswith("regnav:"))
async def reg_navigate(callback: types.CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    try:
        idx = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer()
        return
    if 0 <= idx < len(COMPANY_STRUCTURE):
        await state.update_data(current_dept=COMPANY_STRUCTURE[idx])
    text, kb = await _nav_view(state, lang)
    await _safe_edit(callback, text, kb)
    await callback.answer()


@router.callback_query(RegistrationState.navigating, F.data == "regback")
async def reg_back(callback: types.CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    current = (await state.get_data()).get("current_dept")
    parent = get_parent_department(current) if current else None
    await state.update_data(current_dept=parent)
    text, kb = await _nav_view(state, lang)
    await _safe_edit(callback, text, kb)
    await callback.answer()


@router.callback_query(RegistrationState.navigating, F.data.startswith("regpick:"))
async def reg_pick_self(callback: types.CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    try:
        uid = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer()
        return

    user = await get_user_by_id(uid)
    if not user or user.approval_status != "directory" or user.telegram_id is not None:
        await callback.answer(get_text("reg_already_claimed", lang), show_alert=True)
        text, kb = await _nav_view(state, lang)
        await _safe_edit(callback, text, kb)
        return

    await state.update_data(claimed_user_id=uid)
    prompt = get_text("reg_self_confirm_prompt", lang).format(
        full_name=user.full_name,
        position=user.position or "-",
        department=display_name(user.department) if user.department else "-",
    )
    await _safe_edit(callback, prompt, get_reg_self_confirm_kb(uid, lang))
    await state.set_state(RegistrationState.confirm_self)
    await callback.answer()


@router.callback_query(RegistrationState.confirm_self, F.data == "regnavstay")
async def reg_nav_stay(callback: types.CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    await state.update_data(claimed_user_id=None)
    await state.set_state(RegistrationState.navigating)
    text, kb = await _nav_view(state, lang)
    await _safe_edit(callback, text, kb)
    await callback.answer()


@router.callback_query(RegistrationState.confirm_self, F.data.startswith("regconfirm:"))
async def reg_confirm_self(callback: types.CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    try:
        uid = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer()
        return

    user = await get_user_by_id(uid)
    if not user or user.approval_status != "directory" or user.telegram_id is not None:
        await callback.answer(get_text("reg_already_claimed", lang), show_alert=True)
        await state.update_data(claimed_user_id=None)
        await state.set_state(RegistrationState.navigating)
        text, kb = await _nav_view(state, lang)
        await _safe_edit(callback, text, kb)
        return

    # Данные профиля (ФИО, должность, подразделение, роль, дата рождения) берём из
    # справочника — остаётся собрать авто и фото для Face ID.
    await callback.message.answer(get_text("car_info_prompt", lang))
    await state.set_state(RegistrationState.car_info)
    await callback.answer()


@router.callback_query(RegistrationState.navigating, F.data == "regmanual")
async def reg_manual_start(callback: types.CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    current = (await state.get_data()).get("current_dept")
    if not current:
        await callback.answer(get_text("choose_from_list", lang), show_alert=True)
        return
    await state.update_data(subdivision=current, claimed_user_id=None)
    await callback.message.answer(get_text("reg_manual_name_prompt", lang), reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegistrationState.manual_full_name)
    await callback.answer()


@router.message(RegistrationState.navigating)
async def reg_navigating_hint(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    text, kb = await _nav_view(state, lang)
    await message.answer(text, reply_markup=kb)


# --- Ручная регистрация («Меня нет в списке») --------------------------------

@router.message(RegistrationState.manual_full_name, F.text)
async def process_manual_full_name(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    full_name = message.text.strip()
    if not is_valid_full_name(full_name):
        await message.answer(get_text("invalid_full_name", lang))
        return
    await state.update_data(full_name=full_name)
    await message.answer(get_text("status_choose", lang), reply_markup=get_role_kb(lang))
    await state.set_state(RegistrationState.manual_role)


@router.message(RegistrationState.manual_full_name)
async def process_manual_full_name_invalid(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    await message.answer(get_text("only_text_allowed", lang))


@router.message(
    RegistrationState.manual_role,
    F.text.in_(get_text_variants("role_employee") + get_text_variants("role_manager"))
)
async def process_manual_role(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    canonical_role = resolve_choice(ROLE_CHOICES, message.text)
    # В БД всегда сохраняем канонический русский вариант (HR читает в админке)
    role_text_ru = get_text(ROLE_CHOICES[canonical_role], "ru")
    await state.update_data(role_text=role_text_ru)

    await message.answer(get_text("birth_choose", lang), reply_markup=ReplyKeyboardRemove())
    await message.answer(
        get_text("birth_pick_year", lang),
        reply_markup=await DialogCalendar.start_calendar(year=BIRTH_CALENDAR_START_YEAR)
    )
    await state.set_state(RegistrationState.manual_birth)


@router.message(RegistrationState.manual_role)
async def process_manual_role_invalid(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    await message.answer(get_text("choose_from_list", lang))


@router.callback_query(dialog_cal_callback.filter(), RegistrationState.manual_birth)
async def process_manual_birth(callback: types.CallbackQuery, callback_data: dialog_cal_callback, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")

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


@router.message(RegistrationState.manual_birth)
async def process_manual_birth_invalid(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
    await message.answer(get_text("use_calendar", lang))


# --- Общие шаги: авто + фото (claim и manual) --------------------------------

@router.message(RegistrationState.car_info, F.text)
async def process_car_info(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get("chosen_language", "ru")
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
    claimed_id = data.get("claimed_user_id")

    if claimed_id:
        # Занять запись справочника (п.7): привязать Telegram/авто/фото, отправить HR.
        ok = await claim_directory_user(
            claimed_id,
            telegram_id=data["telegram_id"],
            tg_username=data.get("tg_username"),
            language=lang,
            phone=data["phone"],
            car_info=data.get("car_info", "-"),
            face_id_photo=photo_id,
        )
        if not ok:
            await message.answer(get_text("reg_already_claimed", lang))
            await state.clear()
            return
        user = await get_user_by_id(claimed_id)
        role_text_ru = get_text("role_manager", "ru") if user.role == "manager" else get_text("role_employee", "ru")
        reg_data = {
            "full_name": user.full_name,
            "subdivision": user.department or "-",
            "role_text": role_text_ru,
            "phone": user.phone,
            "tg_username": data.get("tg_username"),
            "birth_date": user.birth_date or "-",
            "car_info": user.car_info or "-",
            "face_id_photo": photo_id,
        }
        await send_registration_to_hr(message.bot, claimed_id, reg_data)
        action_logger.info("registration_claimed user_id=%s", claimed_id)
    else:
        # Ручная регистрация: создаём новую заявку (subdivision/full_name/role_text уже в data).
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
