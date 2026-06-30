# bot/handlers/auth.py
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from bot.utils.db_api import get_user_by_telegram_id, get_user_by_phone, update_user_telegram_id, create_pending_user
from bot.handlers.main_menu import get_main_keyboard

router = Router()


class RegistrationState(StatesGroup):
    full_name = State()
    department = State()
    position = State()
    birth_date = State()
    car_info = State()
    photo = State()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if user:
        if user.approval_status == "pending":
            await message.answer("Ваша анкета находится на рассмотрении HR.")
        elif user.approval_status == "rejected":
            await message.answer("В регистрации отказано. Обратитесь в отдел кадров.")
        else:
            await message.answer("Главное меню", reply_markup=get_main_keyboard())
    else:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отправить номер телефона", request_contact=True)]],
            resize_keyboard=True
        )
        await message.answer("Система HR. Требуется идентификация по номеру телефона.", reply_markup=kb)


@router.message(F.contact)
async def process_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number.replace("+", "")
    user = await get_user_by_phone(phone)

    if user:
        await update_user_telegram_id(user.id, message.from_user.id)
        await message.answer("Идентификация успешна.", reply_markup=get_main_keyboard())
    else:
        await state.update_data(
            phone=phone,
            telegram_id=message.from_user.id,
            tg_username=message.from_user.username
        )
        await message.answer(
            "Сотрудник не найден в базе. Начат процесс регистрации.\n\nВведите ФИО (по паспорту на латинице):",
            reply_markup=ReplyKeyboardRemove())
        await state.set_state(RegistrationState.full_name)


@router.message(RegistrationState.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Укажите Управление/Отдел:")
    await state.set_state(RegistrationState.department)


@router.message(RegistrationState.department)
async def process_department(message: types.Message, state: FSMContext):
    await state.update_data(department=message.text)
    await message.answer("Укажите должность:")
    await state.set_state(RegistrationState.position)


@router.message(RegistrationState.position)
async def process_position(message: types.Message, state: FSMContext):
    await state.update_data(position=message.text)
    await message.answer("Укажите дату рождения (ДД.ММ.ГГГГ):")
    await state.set_state(RegistrationState.birth_date)


@router.message(RegistrationState.birth_date)
async def process_birth_date(message: types.Message, state: FSMContext):
    await state.update_data(birth_date=message.text)
    await message.answer("Укажите номер и марку автомобиля (или отправьте '-' если нет):")
    await state.set_state(RegistrationState.car_info)


@router.message(RegistrationState.car_info)
async def process_car_info(message: types.Message, state: FSMContext):
    await state.update_data(car_info=message.text)
    await message.answer("Загрузите фото для Face ID:")
    await state.set_state(RegistrationState.photo)


@router.message(RegistrationState.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.update_data(face_id_photo=photo_id)

    user_id = await create_pending_user(data)

    from bot.utils.routing import send_registration_to_hr
    await send_registration_to_hr(message.bot, user_id, data)

    await message.answer("Анкета отправлена в HR. Ожидайте уведомления о результатах проверки.")
    await state.clear()