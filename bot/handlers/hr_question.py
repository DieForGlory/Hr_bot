from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.utils.db_api import get_users_by_role, get_user_by_telegram_id, get_user_by_id
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


class HRQuestionState(StatesGroup):
    waiting_for_question = State()
    waiting_for_reply = State()


@router.message(F.text == "Вопрос HR")
async def ask_hr_start(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш вопрос для HR-отдела:")
    await state.set_state(HRQuestionState.waiting_for_question)


@router.message(HRQuestionState.waiting_for_question)
async def process_question(message: types.Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    hr_users = await get_users_by_role("hr")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ответить", callback_data=f"hr_reply_{user.id}")]
    ])

    text = f"❓ Вопрос от {user.full_name} ({user.department}):\n\n{message.text}"

    for hr in hr_users:
        if hr.telegram_id:
            await message.bot.send_message(hr.telegram_id, text, reply_markup=kb)

    await message.answer("Вопрос передан в HR-отдел.")
    await state.clear()


@router.callback_query(F.data.startswith("hr_reply_"))
async def process_hr_reply_start(callback: types.CallbackQuery, state: FSMContext):
    target_user_id = int(callback.data.split("_")[2])
    await state.update_data(target_user_id=target_user_id)
    await callback.message.answer("Введите текст ответа:")
    await state.set_state(HRQuestionState.waiting_for_reply)
    await callback.answer()


@router.message(HRQuestionState.waiting_for_reply)
async def process_hr_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_user = await get_user_by_id(data['target_user_id'])

    if target_user and target_user.telegram_id:
        await message.bot.send_message(
            target_user.telegram_id,
            f"Ответ от HR:\n\n{message.text}"
        )
        await message.answer("Ответ отправлен сотруднику.")
    else:
        await message.answer("Ошибка: сотрудник не найден или не авторизован.")

    await state.clear()