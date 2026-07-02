from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.utils.db_api import get_user_by_telegram_id, create_request
from bot.utils.routing import route_certificate
from bot.utils.validators import parse_callback_id, clean_text, MAX_COMMENT_LEN
from bot.locales.texts import get_text, get_text_variants, resolve_choice
from core.logging_config import action_logger
from bot.services.request_actions import (
    set_cert_status, send_cert_ready_notice, RequestNotFound, CommentRequired,
)

router = Router()

CERT_CHOICES = {"income_cert": "cert_income", "work_cert": "cert_work"}


class CertState(StatesGroup):
    waiting_for_comment = State()


class CertRejectState(StatesGroup):
    waiting_for_reject_comment = State()


class CertDoneState(StatesGroup):
    waiting_for_attachment = State()


def get_cert_type_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=get_text("cert_income", lang))
    builder.button(text=get_text("cert_work", lang))
    builder.button(text=get_text("back_button", lang))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


@router.message(F.text.in_(get_text_variants("certificates")))
async def cert_menu(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(get_text("cert_choose_type", lang), reply_markup=get_cert_type_kb(lang))


@router.message(F.text.in_(get_text_variants("cert_income") + get_text_variants("cert_work")))
async def process_cert_type(message: types.Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"

    canonical_type = resolve_choice(CERT_CHOICES, message.text)
    await state.update_data(cert_type=canonical_type)
    await message.answer(get_text("cert_ask_comment", lang))
    await state.set_state(CertState.waiting_for_comment)


@router.message(CertState.waiting_for_comment, F.text)
async def process_cert_comment(message: types.Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"

    comment = clean_text(message.text, MAX_COMMENT_LEN)
    if comment is None:
        await message.answer(get_text("text_too_long", lang))
        return

    data = await state.get_data()
    req_type = data.get('cert_type')
    if not user or not req_type:
        await message.answer(get_text("session_expired", lang))
        await state.clear()
        return

    req_id = await create_request(user.id, req_type, comment=comment)
    action_logger.info("request_created type=%s user_id=%s req_id=%s", req_type, user.id, req_id)

    await route_certificate(message.bot, req_id, req_type, user, comment)

    await message.answer(get_text("cert_submitted", lang))
    await state.clear()


@router.message(CertState.waiting_for_comment)
async def process_cert_comment_invalid(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(get_text("only_text_allowed", lang))


@router.callback_query(F.data.startswith("cert_progress_"))
async def process_cert_progress(callback: types.CallbackQuery):
    req_id = parse_callback_id(callback.data)
    if req_id is None:
        await callback.answer()
        return

    actor = await get_user_by_telegram_id(callback.from_user.id)
    actor_lang = actor.language if actor else "ru"
    try:
        await set_cert_status(callback.bot, req_id, "in_progress", actor=actor)
    except RequestNotFound:
        await callback.answer(get_text("request_not_found", actor_lang), show_alert=True)
        return

    await callback.message.edit_text(callback.message.text + get_text("cert_progress_suffix", actor_lang))
    await callback.answer()


@router.callback_query(F.data.startswith("cert_done_"))
async def process_cert_done(callback: types.CallbackQuery, state: FSMContext):
    req_id = parse_callback_id(callback.data)
    if req_id is None:
        await callback.answer()
        return

    actor = await get_user_by_telegram_id(callback.from_user.id)
    actor_lang = actor.language if actor else "ru"
    try:
        await set_cert_status(callback.bot, req_id, "done", actor=actor)
    except RequestNotFound:
        await callback.answer(get_text("request_not_found", actor_lang), show_alert=True)
        return

    await state.update_data(cert_done_req_id=req_id)
    await callback.message.answer(get_text("cert_pickup_prompt", actor_lang))
    await state.set_state(CertDoneState.waiting_for_attachment)

    await callback.message.edit_text(callback.message.text + get_text("cert_done_suffix", actor_lang))
    await callback.answer()


@router.message(CertDoneState.waiting_for_attachment, F.text | F.photo | F.document)
async def process_cert_done_attachment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    req_id = data.get('cert_done_req_id')
    if req_id is None:
        await state.clear()
        return

    actor = await get_user_by_telegram_id(message.from_user.id)
    actor_lang = actor.language if actor else "ru"

    attachment = None
    pickup_note = None
    if message.document:
        attachment = {"kind": "document", "file_id": message.document.file_id}
    elif message.photo:
        attachment = {"kind": "photo", "file_id": message.photo[-1].file_id}
    elif message.text and message.text.strip() != "-":
        pickup_note = message.text.strip()[:MAX_COMMENT_LEN]

    try:
        await send_cert_ready_notice(message.bot, req_id, actor=actor, attachment=attachment, pickup_note=pickup_note)
    except RequestNotFound:
        await state.clear()
        return

    await message.answer(get_text("cert_notified_ready", actor_lang))
    await state.clear()


@router.message(CertDoneState.waiting_for_attachment)
async def process_cert_done_attachment_invalid(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(get_text("cert_attachment_prompt_invalid", lang))


@router.callback_query(F.data.startswith("cert_reject_"))
async def process_cert_reject_init(callback: types.CallbackQuery, state: FSMContext):
    req_id = parse_callback_id(callback.data)
    if req_id is None:
        await callback.answer()
        return

    actor = await get_user_by_telegram_id(callback.from_user.id)
    actor_lang = actor.language if actor else "ru"

    await state.update_data(cert_reject_req_id=req_id)
    await callback.message.answer(get_text("approval_reject_prompt", actor_lang))
    await state.set_state(CertRejectState.waiting_for_reject_comment)
    await callback.answer()


@router.message(CertRejectState.waiting_for_reject_comment, F.text)
async def process_cert_reject_comment(message: types.Message, state: FSMContext):
    actor = await get_user_by_telegram_id(message.from_user.id)
    actor_lang = actor.language if actor else "ru"

    comment = clean_text(message.text, MAX_COMMENT_LEN)
    if comment is None:
        await message.answer(get_text("text_too_long", actor_lang))
        return

    data = await state.get_data()
    req_id = data.get('cert_reject_req_id')
    if req_id is None:
        await state.clear()
        return

    try:
        await set_cert_status(message.bot, req_id, "rejected", actor=actor, comment=comment)
    except RequestNotFound:
        await message.answer(get_text("request_not_found", actor_lang))
        await state.clear()
        return
    except CommentRequired:
        await message.answer(get_text("approval_comment_required", actor_lang))
        return

    await message.answer(get_text("approval_rejected_notified", actor_lang))
    await state.clear()


@router.message(CertRejectState.waiting_for_reject_comment)
async def process_cert_reject_comment_invalid(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(get_text("only_text_allowed", lang))
