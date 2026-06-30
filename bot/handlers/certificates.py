from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.utils.db_api import get_user_by_telegram_id, create_request
from bot.utils.routing import route_certificate

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
        "Например: справка для посольства, дата посещения и т.д."
    )
    await state.set_state(CertState.waiting_for_comment)


@router.message(CertState.waiting_for_comment)
async def process_cert_comment(message: types.Message, state: FSMContext):
    data = await state.update_data(comment=message.text)
    user = await get_user_by_telegram_id(message.from_user.id)

    req_type = "income_cert" if data['cert_type'] == "Справка о доходах" else "work_cert"
    req_id = await create_request(user.id, req_type, comment=data['comment'])

    await route_certificate(message.bot, req_id, data['cert_type'], user, data['comment'])

    await message.answer("Ваша заявка принята в обработку.")
    await state.clear()