from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.utils.db_api import get_user_by_telegram_id, get_user_by_id, get_request_by_id, create_request, update_request_status
from bot.utils.routing import route_certificate
from bot.utils.validators import parse_callback_id, clean_text, MAX_COMMENT_LEN
from bot.locales.texts import get_text
from core.logging_config import action_logger

router = Router()


class CertState(StatesGroup):
    waiting_for_comment = State()


class CertRejectState(StatesGroup):
    waiting_for_reject_comment = State()


class CertDoneState(StatesGroup):
    waiting_for_attachment = State()


def get_cert_type_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Справка о доходах")
    builder.button(text="Справка с места работы")
    builder.button(text="Назад")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


@router.message(F.text == "💰 Справки")
async def cert_menu(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(get_text("cert_choose_type", lang), reply_markup=get_cert_type_kb())


@router.message(F.text.in_(["Справка о доходах", "Справка с места работы"]))
async def process_cert_type(message: types.Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await state.update_data(cert_type=message.text)
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
    cert_type = data.get('cert_type')
    if not user or not cert_type:
        await message.answer(get_text("session_expired", lang))
        await state.clear()
        return

    req_type = "income_cert" if cert_type == "Справка о доходах" else "work_cert"
    req_id = await create_request(user.id, req_type, comment=comment)
    action_logger.info("request_created type=%s user_id=%s req_id=%s", req_type, user.id, req_id)

    await route_certificate(message.bot, req_id, cert_type, user, comment)

    await message.answer(get_text("cert_submitted", user.language))
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

    req = await get_request_by_id(req_id)
    if not req:
        await callback.answer(get_text("request_not_found", "ru"), show_alert=True)
        return

    await update_request_status(req_id, "in_progress")
    action_logger.info("cert_status_change req_id=%s status=in_progress", req_id)

    employee = await get_user_by_id(req.user_id)
    if employee and employee.telegram_id:
        await callback.bot.send_message(employee.telegram_id, "Ваша справка взята в работу.")

    await callback.message.edit_text(callback.message.text + "\n\n🔄 В работе")
    await callback.answer()


@router.callback_query(F.data.startswith("cert_done_"))
async def process_cert_done(callback: types.CallbackQuery, state: FSMContext):
    req_id = parse_callback_id(callback.data)
    if req_id is None:
        await callback.answer()
        return

    req = await get_request_by_id(req_id)
    if not req:
        await callback.answer(get_text("request_not_found", "ru"), show_alert=True)
        return

    await update_request_status(req_id, "done")
    action_logger.info("cert_status_change req_id=%s status=done", req_id)

    await state.update_data(cert_done_req_id=req_id)
    await callback.message.answer(
        "При необходимости пришлите PDF/фото справки или укажите место получения текстом.\n"
        "Если это не требуется — отправьте «-»."
    )
    await state.set_state(CertDoneState.waiting_for_attachment)

    await callback.message.edit_text(callback.message.text + "\n\n✅ Готово")
    await callback.answer()


@router.message(CertDoneState.waiting_for_attachment, F.text | F.photo | F.document)
async def process_cert_done_attachment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    req_id = data.get('cert_done_req_id')
    if req_id is None:
        await state.clear()
        return

    req = await get_request_by_id(req_id)
    if not req:
        await state.clear()
        return
    employee = await get_user_by_id(req.user_id)

    if employee and employee.telegram_id:
        await message.bot.send_message(employee.telegram_id, get_text("cert_ready", employee.language))

        if message.document:
            await message.bot.send_document(employee.telegram_id, message.document.file_id)
        elif message.photo:
            await message.bot.send_photo(employee.telegram_id, message.photo[-1].file_id)
        elif message.text and message.text.strip() != "-":
            await message.bot.send_message(employee.telegram_id, f"Место получения: {message.text.strip()[:MAX_COMMENT_LEN]}")

    await message.answer("Сотрудник уведомлен о готовности справки.")
    await state.clear()


@router.message(CertDoneState.waiting_for_attachment)
async def process_cert_done_attachment_invalid(message: types.Message):
    await message.answer("Пришлите PDF/фото, текст с местом получения или «-».")


@router.callback_query(F.data.startswith("cert_reject_"))
async def process_cert_reject_init(callback: types.CallbackQuery, state: FSMContext):
    req_id = parse_callback_id(callback.data)
    if req_id is None:
        await callback.answer()
        return

    await state.update_data(cert_reject_req_id=req_id)
    await callback.message.answer("Отказ требует комментария. Введите причину отклонения:")
    await state.set_state(CertRejectState.waiting_for_reject_comment)
    await callback.answer()


@router.message(CertRejectState.waiting_for_reject_comment, F.text)
async def process_cert_reject_comment(message: types.Message, state: FSMContext):
    comment = clean_text(message.text, MAX_COMMENT_LEN)
    if comment is None:
        await message.answer(get_text("text_too_long", "ru"))
        return

    data = await state.get_data()
    req_id = data.get('cert_reject_req_id')
    if req_id is None:
        await state.clear()
        return

    req = await get_request_by_id(req_id)
    if not req:
        await message.answer(get_text("request_not_found", "ru"))
        await state.clear()
        return

    await update_request_status(req_id, "rejected", hr_comment=comment)
    action_logger.info("cert_status_change req_id=%s status=rejected", req_id)

    employee = await get_user_by_id(req.user_id)
    if employee and employee.telegram_id:
        await message.bot.send_message(
            employee.telegram_id,
            f"Заявка на справку отклонена.\nКомментарий: {comment}"
        )

    await message.answer("Заявка отклонена, сотрудник уведомлен.")
    await state.clear()


@router.message(CertRejectState.waiting_for_reject_comment)
async def process_cert_reject_comment_invalid(message: types.Message):
    await message.answer(get_text("only_text_allowed", "ru"))
