from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.utils.db_api import get_users_by_role, get_user_by_telegram_id, get_user_by_id
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.validators import parse_callback_id, clean_text, MAX_QUESTION_LEN
from bot.locales.texts import get_text
from core.logging_config import action_logger

router = Router()


class HRQuestionState(StatesGroup):
    waiting_for_question = State()
    waiting_for_reply = State()


@router.message(F.text == "Вопрос HR")
async def ask_hr_start(message: types.Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(get_text("hr_question_prompt", lang))
    await state.set_state(HRQuestionState.waiting_for_question)


@router.message(HRQuestionState.waiting_for_question, F.text)
async def process_question(message: types.Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await state.clear()
        return

    question = clean_text(message.text, MAX_QUESTION_LEN)
    if question is None:
        await message.answer(get_text("text_too_long", user.language))
        return

    hr_users = await get_users_by_role("hr")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ответить", callback_data=f"hr_reply_{user.id}")]
    ])

    text = f"❓ Вопрос от {user.full_name} ({user.department}):\n\n{question}"

    for hr in hr_users:
        if hr.telegram_id:
            await message.bot.send_message(hr.telegram_id, text, reply_markup=kb)

    action_logger.info("hr_question_asked user_id=%s", user.id)
    await message.answer(get_text("hr_question_sent", user.language))
    await state.clear()


@router.message(HRQuestionState.waiting_for_question)
async def process_question_invalid(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(get_text("only_text_allowed", lang))


@router.callback_query(F.data.startswith("hr_reply_"))
async def process_hr_reply_start(callback: types.CallbackQuery, state: FSMContext):
    target_user_id = parse_callback_id(callback.data)
    if target_user_id is None:
        await callback.answer()
        return

    await state.update_data(target_user_id=target_user_id)
    await callback.message.answer("Введите текст ответа:")
    await state.set_state(HRQuestionState.waiting_for_reply)
    await callback.answer()


@router.message(HRQuestionState.waiting_for_reply, F.text)
async def process_hr_reply(message: types.Message, state: FSMContext):
    reply = clean_text(message.text, MAX_QUESTION_LEN)
    if reply is None:
        await message.answer(get_text("text_too_long", "ru"))
        return

    data = await state.get_data()
    target_user_id = data.get('target_user_id')
    target_user = await get_user_by_id(target_user_id) if target_user_id else None

    if target_user and target_user.telegram_id:
        await message.bot.send_message(
            target_user.telegram_id,
            f"Ответ от HR:\n\n{reply}"
        )
        action_logger.info("hr_question_answered target_user_id=%s", target_user.id)
        await message.answer("Ответ отправлен сотруднику.")
    else:
        await message.answer("Ошибка: сотрудник не найден или не авторизован.")

    await state.clear()


@router.message(HRQuestionState.waiting_for_reply)
async def process_hr_reply_invalid(message: types.Message):
    await message.answer(get_text("only_text_allowed", "ru"))