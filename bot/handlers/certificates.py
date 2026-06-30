
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()


class CertState(StatesGroup):
    waiting_for_comment = State()


def get_cert_type_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Справка о доходах")
    builder.button(text="Справка с места работы")
    builder.button(text="Назад")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


@router.message(F.text == "💰 Справки")
async def cert_menu(message: types.Message):
    await message.answer("Выберите тип справки:", reply_markup=get_cert_type_kb())


@router.message(F.text.in_(["Справка о доходах", "Справка с места работы"]))
async def process_cert_type(message: types.Message, state: FSMContext):
    await state.update_data(cert_type=message.text)
    await message.answer(
        "При необходимости укажите дополнительную информацию.\n"
        "Например: справка для посольства, дата посещения и т.д.\n"
        "Или отправьте '-' если комментарий не нужен."
    )
    await state.set_state(CertState.waiting_for_comment)


@router.message(CertState.waiting_for_comment)
async def process_cert_comment(message: types.Message, state: FSMContext):
    data = await state.update_data(comment=message.text)
    await message.answer("Ваша заявка принята в обработку.")
    await state.clear()

    from bot.handlers.main_menu import get_main_keyboard
    await message.answer("Главное меню", reply_markup=get_main_keyboard())