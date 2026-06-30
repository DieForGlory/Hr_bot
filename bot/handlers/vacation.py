
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()


class VacationState(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_end_date = State()
    confirm = State()


def get_vacation_type_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Заявка на ежегодный оплачиваемый отпуск")
    builder.button(text="Заявка на отпуск без содержания")
    builder.button(text="Назад")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


@router.message(F.text == "📄 Отпуск")
async def vacation_menu(message: types.Message):
    await message.answer("Выберите тип отпуска:", reply_markup=get_vacation_type_kb())


@router.message(F.text.in_(["Заявка на ежегодный оплачиваемый отпуск", "Заявка на отпуск без содержания"]))
async def start_vacation_request(message: types.Message, state: FSMContext):
    await state.update_data(vacation_type=message.text)
    await message.answer("Введите дату начала отпуска (ДД.ММ.ГГГГ):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(VacationState.waiting_for_start_date)


@router.message(VacationState.waiting_for_start_date)
async def process_start_date(message: types.Message, state: FSMContext):
    await state.update_data(start_date=message.text)
    await message.answer("Введите дату окончания отпуска (ДД.ММ.ГГГГ):")
    await state.set_state(VacationState.waiting_for_end_date)


@router.message(VacationState.waiting_for_end_date)
async def process_end_date(message: types.Message, state: FSMContext):
    data = await state.update_data(end_date=message.text)
    builder = ReplyKeyboardBuilder()
    builder.button(text="Отправить заявку")
    builder.button(text="Отмена")
    builder.adjust(2)

    await message.answer(
        f"Подтверждение:\nТип: {data['vacation_type']}\nПериод: {data['start_date']} - {data['end_date']}",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    await state.set_state(VacationState.confirm)


@router.message(VacationState.confirm, F.text == "Отправить заявку")
async def confirm_vacation(message: types.Message, state: FSMContext):
    await message.answer("Ваша заявка принята и направлена на согласование.")
    await state.clear()

    from bot.handlers.main_menu import get_main_keyboard
    await message.answer("Главное меню", reply_markup=get_main_keyboard())


@router.message(F.text == "Отмена")
@router.message(F.text == "Назад")
async def cancel_action(message: types.Message, state: FSMContext):
    await state.clear()
    from bot.handlers.main_menu import get_main_keyboard
    await message.answer("Главное меню", reply_markup=get_main_keyboard())