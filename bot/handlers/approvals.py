# bot/handlers/approvals.py
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile
from bot.utils.db_api import get_request_by_id, update_request_status, get_user_by_id, get_users_by_role, update_user_approval
from bot.utils.pdf_gen import generate_vacation_pdf
from bot.keyboards.inline import get_approval_keyboard
from bot.utils.routing import notify_hr_vacation_approved
from bot.utils.validators import parse_callback_id, clean_text, MAX_COMMENT_LEN
from bot.locales.texts import get_text
from core.logging_config import action_logger

router = Router()


class ApprovalState(StatesGroup):
    waiting_for_reject_comment = State()
    waiting_for_approve_comment = State()


@router.callback_query(F.data.startswith("reg_approve_"))
async def process_reg_approve(callback: types.CallbackQuery):
    user_id = parse_callback_id(callback.data)
    if user_id is None:
        await callback.answer()
        return

    user = await get_user_by_id(user_id)
    if not user:
        await callback.answer(get_text("request_not_found", "ru"), show_alert=True)
        return

    await update_user_approval(user_id, "approved")

    if user.telegram_id:
        from bot.handlers.main_menu import get_main_keyboard
        await callback.bot.send_message(
            user.telegram_id,
            "Ваша учетная запись подтверждена. Доступ к системе открыт.",
            reply_markup=get_main_keyboard(user.language)
        )

    action_logger.info("registration_approved user_id=%s", user_id)
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ Одобрено")
    await callback.answer()


@router.callback_query(F.data.startswith("reg_reject_"))
async def process_reg_reject(callback: types.CallbackQuery):
    user_id = parse_callback_id(callback.data)
    if user_id is None:
        await callback.answer()
        return

    user = await get_user_by_id(user_id)
    if not user:
        await callback.answer(get_text("request_not_found", "ru"), show_alert=True)
        return

    await update_user_approval(user_id, "rejected")

    if user.telegram_id:
        await callback.bot.send_message(
            user.telegram_id,
            "В регистрации отказано."
        )

    action_logger.info("registration_rejected user_id=%s", user_id)
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ Отклонено")
    await callback.answer()


async def _do_approve(bot, req_id: int, comment: str = None):
    req = await get_request_by_id(req_id)
    if not req:
        return
    employee = await get_user_by_id(req.user_id)
    if not employee:
        return

    if req.status == "pending":
        await update_request_status(req_id, "manager_approved", manager_comment=comment)
        req = await get_request_by_id(req_id)
        action_logger.info("request_manager_approved req_id=%s", req_id)

        await notify_hr_vacation_approved(bot, employee, req)

    elif req.status == "manager_approved":
        await update_request_status(req_id, "hr_approved", hr_comment=comment)
        req = await get_request_by_id(req_id)
        action_logger.info("request_hr_approved req_id=%s", req_id)

        pdf_path = await generate_vacation_pdf(
            req.id, employee.full_name, req.start_date, req.end_date, req.type,
            department=employee.department, days_count=req.days_count
        )

        if employee.telegram_id:
            await bot.send_message(
                employee.telegram_id,
                get_text("vacation_approved_final", employee.language)
            )
            document = FSInputFile(pdf_path)
            await bot.send_document(employee.telegram_id, document)


@router.callback_query(F.data.startswith("approve_"))
async def process_approve(callback: types.CallbackQuery):
    req_id = parse_callback_id(callback.data)
    if req_id is None:
        await callback.answer()
        return

    req = await get_request_by_id(req_id)
    if not req:
        await callback.answer(get_text("request_not_found", "ru"), show_alert=True)
        return
    suffix = "\n\n✅ Согласовано руководителем." if req.status == "pending" else "\n\n✅ Согласовано HR."

    await _do_approve(callback.bot, req_id)
    await callback.message.edit_text(callback.message.text + suffix)
    await callback.answer()


@router.callback_query(F.data.startswith("comment_"))
async def process_comment_init(callback: types.CallbackQuery, state: FSMContext):
    req_id = parse_callback_id(callback.data)
    if req_id is None:
        await callback.answer()
        return

    await state.update_data(approve_req_id=req_id)
    await callback.message.answer("Введите комментарий к согласованию:")
    await state.set_state(ApprovalState.waiting_for_approve_comment)
    await callback.answer()


@router.message(ApprovalState.waiting_for_approve_comment, F.text)
async def process_approve_comment(message: types.Message, state: FSMContext):
    comment = clean_text(message.text, MAX_COMMENT_LEN)
    if comment is None:
        await message.answer(get_text("text_too_long", "ru"))
        return

    data = await state.get_data()
    req_id = data.get('approve_req_id')
    if req_id is None:
        await state.clear()
        return

    await _do_approve(message.bot, req_id, comment=comment)
    await message.answer("Заявка согласована с комментарием.")
    await state.clear()


@router.message(ApprovalState.waiting_for_approve_comment)
async def process_approve_comment_invalid(message: types.Message):
    await message.answer(get_text("only_text_allowed", "ru"))


@router.callback_query(F.data.startswith("reject_"))
async def process_reject_init(callback: types.CallbackQuery, state: FSMContext):
    req_id = parse_callback_id(callback.data)
    if req_id is None:
        await callback.answer()
        return

    await state.update_data(reject_req_id=req_id, origin_message_id=callback.message.message_id)
    await callback.message.answer("Отказ требует комментария. Введите причину отклонения:")
    await state.set_state(ApprovalState.waiting_for_reject_comment)
    await callback.answer()


@router.message(ApprovalState.waiting_for_reject_comment, F.text)
async def process_reject_comment(message: types.Message, state: FSMContext):
    comment = clean_text(message.text, MAX_COMMENT_LEN)
    if comment is None:
        await message.answer(get_text("text_too_long", "ru"))
        return

    data = await state.get_data()
    req_id = data.get('reject_req_id')
    if req_id is None:
        await state.clear()
        return

    req = await get_request_by_id(req_id)
    if not req:
        await message.answer(get_text("request_not_found", "ru"))
        await state.clear()
        return
    employee = await get_user_by_id(req.user_id)

    await update_request_status(req_id, "rejected", hr_comment=comment)
    action_logger.info("request_rejected req_id=%s", req_id)

    if employee and employee.telegram_id:
        await message.bot.send_message(
            employee.telegram_id,
            f"{get_text('vacation_rejected', employee.language)}\nКомментарий: {comment}"
        )

    await message.answer("Заявка отклонена, сотрудник уведомлен.")
    await state.clear()


@router.message(ApprovalState.waiting_for_reject_comment)
async def process_reject_comment_invalid(message: types.Message):
    await message.answer(get_text("only_text_allowed", "ru"))
