from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.utils.db_api import get_users_by_role, get_user_by_telegram_id, get_user_by_id
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.validators import parse_callback_id, clean_text, MAX_QUESTION_LEN
from bot.locales.texts import get_text, get_text_variants
from core.logging_config import action_logger

router = Router()


class HRQuestionState(StatesGroup):
    waiting_for_question = State()
    waiting_for_reply = State()


@router.message(F.text.in_(get_text_variants("hr_question")))
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

    from bot.utils.notify_window import dispatch_notification
    for hr in hr_users:
        if hr.telegram_id:
            text = get_text("hr_question_header", hr.language).format(
                name=user.full_name, department=user.department, question=question
            )
            await dispatch_notification(
                message.bot, hr.telegram_id, text, hr.language,
                kb_kind="hr_reply", kb_ref_id=user.id,
                context=f"hr_question user_id={user.id} hr_id={hr.id}",
            )

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

    actor = await get_user_by_telegram_id(callback.from_user.id)
    actor_lang = actor.language if actor else "ru"

    await state.update_data(target_user_id=target_user_id)
    await callback.message.answer(get_text("hr_reply_prompt", actor_lang))
    await state.set_state(HRQuestionState.waiting_for_reply)
    await callback.answer()


@router.message(HRQuestionState.waiting_for_reply, F.text)
async def process_hr_reply(message: types.Message, state: FSMContext):
    actor = await get_user_by_telegram_id(message.from_user.id)
    actor_lang = actor.language if actor else "ru"

    reply = clean_text(message.text, MAX_QUESTION_LEN)
    if reply is None:
        await message.answer(get_text("text_too_long", actor_lang))
        return

    data = await state.get_data()
    target_user_id = data.get('target_user_id')
    target_user = await get_user_by_id(target_user_id) if target_user_id else None

    if target_user and target_user.telegram_id:
        await message.bot.send_message(
            target_user.telegram_id,
            get_text("hr_answer_prefix", target_user.language).format(reply=reply)
        )
        action_logger.info("hr_question_answered target_user_id=%s", target_user.id)
        await message.answer(get_text("hr_reply_sent_confirm", actor_lang))
    else:
        await message.answer(get_text("hr_reply_error", actor_lang))

    await state.clear()


@router.message(HRQuestionState.waiting_for_reply)
async def process_hr_reply_invalid(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(get_text("only_text_allowed", lang))
