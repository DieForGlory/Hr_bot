# bot/handlers/approvals.py
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.utils.db_api import get_user_by_telegram_id
from bot.utils.validators import parse_callback_id, clean_text, MAX_COMMENT_LEN
from bot.locales.texts import get_text
from bot.services.request_actions import (
    approve_registration, reject_registration, approve_request, reject_request,
    RequestNotFound, UserNotFound, CommentRequired, InvalidTransition,
)

router = Router()


class ApprovalState(StatesGroup):
    waiting_for_reject_comment = State()
    waiting_for_approve_comment = State()


async def _actor_lang(telegram_id: int) -> str:
    actor = await get_user_by_telegram_id(telegram_id)
    return actor.language if actor else "ru"


@router.callback_query(F.data.startswith("reg_approve_"))
async def process_reg_approve(callback: types.CallbackQuery):
    user_id = parse_callback_id(callback.data)
    if user_id is None:
        await callback.answer()
        return

    actor = await get_user_by_telegram_id(callback.from_user.id)
    actor_lang = actor.language if actor else "ru"
    try:
        await approve_registration(callback.bot, user_id, actor=actor)
    except UserNotFound:
        await callback.answer(get_text("request_not_found", actor_lang), show_alert=True)
        return

    await callback.message.edit_caption(caption=callback.message.caption + get_text("reg_approved_admin_suffix", actor_lang))
    await callback.answer()


@router.callback_query(F.data.startswith("reg_reject_"))
async def process_reg_reject(callback: types.CallbackQuery):
    user_id = parse_callback_id(callback.data)
    if user_id is None:
        await callback.answer()
        return

    actor = await get_user_by_telegram_id(callback.from_user.id)
    actor_lang = actor.language if actor else "ru"
    try:
        await reject_registration(callback.bot, user_id, actor=actor)
    except UserNotFound:
        await callback.answer(get_text("request_not_found", actor_lang), show_alert=True)
        return

    await callback.message.edit_caption(caption=callback.message.caption + get_text("reg_rejected_admin_suffix", actor_lang))
    await callback.answer()


@router.callback_query(F.data.startswith("approve_"))
async def process_approve(callback: types.CallbackQuery):
    req_id = parse_callback_id(callback.data)
    if req_id is None:
        await callback.answer()
        return

    actor = await get_user_by_telegram_id(callback.from_user.id)
    actor_lang = actor.language if actor else "ru"
    try:
        req, stage = await approve_request(callback.bot, req_id, actor=actor)
    except RequestNotFound:
        await callback.answer(get_text("request_not_found", actor_lang), show_alert=True)
        return
    except InvalidTransition:
        await callback.answer(get_text("approval_already_processed", actor_lang), show_alert=True)
        return

    suffix_key = "approval_manager_done_suffix" if stage == "manager" else "approval_hr_done_suffix"
    await callback.message.edit_text(callback.message.text + get_text(suffix_key, actor_lang))
    await callback.answer()


@router.callback_query(F.data.startswith("comment_"))
async def process_comment_init(callback: types.CallbackQuery, state: FSMContext):
    req_id = parse_callback_id(callback.data)
    if req_id is None:
        await callback.answer()
        return

    actor_lang = await _actor_lang(callback.from_user.id)
    await state.update_data(approve_req_id=req_id)
    await callback.message.answer(get_text("approval_comment_prompt", actor_lang))
    await state.set_state(ApprovalState.waiting_for_approve_comment)
    await callback.answer()


@router.message(ApprovalState.waiting_for_approve_comment, F.text)
async def process_approve_comment(message: types.Message, state: FSMContext):
    actor = await get_user_by_telegram_id(message.from_user.id)
    actor_lang = actor.language if actor else "ru"

    comment = clean_text(message.text, MAX_COMMENT_LEN)
    if comment is None:
        await message.answer(get_text("text_too_long", actor_lang))
        return

    data = await state.get_data()
    req_id = data.get('approve_req_id')
    if req_id is None:
        await state.clear()
        return

    try:
        await approve_request(message.bot, req_id, actor=actor, comment=comment)
    except (RequestNotFound, UserNotFound):
        await message.answer(get_text("request_not_found", actor_lang))
        await state.clear()
        return
    except InvalidTransition:
        await message.answer(get_text("approval_already_processed", actor_lang))
        await state.clear()
        return

    await message.answer(get_text("approval_approved_with_comment", actor_lang))
    await state.clear()


@router.message(ApprovalState.waiting_for_approve_comment)
async def process_approve_comment_invalid(message: types.Message):
    lang = await _actor_lang(message.from_user.id)
    await message.answer(get_text("only_text_allowed", lang))


@router.callback_query(F.data.startswith("reject_"))
async def process_reject_init(callback: types.CallbackQuery, state: FSMContext):
    req_id = parse_callback_id(callback.data)
    if req_id is None:
        await callback.answer()
        return

    actor_lang = await _actor_lang(callback.from_user.id)
    await state.update_data(reject_req_id=req_id, origin_message_id=callback.message.message_id)
    await callback.message.answer(get_text("approval_reject_prompt", actor_lang))
    await state.set_state(ApprovalState.waiting_for_reject_comment)
    await callback.answer()


@router.message(ApprovalState.waiting_for_reject_comment, F.text)
async def process_reject_comment(message: types.Message, state: FSMContext):
    actor = await get_user_by_telegram_id(message.from_user.id)
    actor_lang = actor.language if actor else "ru"

    comment = clean_text(message.text, MAX_COMMENT_LEN)
    if comment is None:
        await message.answer(get_text("text_too_long", actor_lang))
        return

    data = await state.get_data()
    req_id = data.get('reject_req_id')
    if req_id is None:
        await state.clear()
        return

    try:
        await reject_request(message.bot, req_id, actor=actor, comment=comment)
    except RequestNotFound:
        await message.answer(get_text("request_not_found", actor_lang))
        await state.clear()
        return
    except CommentRequired:
        await message.answer(get_text("approval_comment_required", actor_lang))
        return

    await message.answer(get_text("approval_rejected_notified", actor_lang))
    await state.clear()


@router.message(ApprovalState.waiting_for_reject_comment)
async def process_reject_comment_invalid(message: types.Message):
    lang = await _actor_lang(message.from_user.id)
    await message.answer(get_text("only_text_allowed", lang))
