# bot/handlers/approvals.py
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile
from bot.utils.db_api import get_request_by_id, update_request_status, get_user_by_id, get_users_by_role
from bot.utils.pdf_gen import generate_vacation_pdf
from bot.keyboards.inline import get_approval_keyboard

router = Router()


class ApprovalState(StatesGroup):
    waiting_for_reject_comment = State()


@router.callback_query(F.data.startswith("approve_"))
async def process_approve(callback: types.CallbackQuery):
    req_id = int(callback.data.split("_")[1])
    req = await get_request_by_id(req_id)
    employee = await get_user_by_id(req.user_id)

    if req.status == "pending":
        await update_request_status(req_id, "manager_approved")
        await callback.message.edit_text(callback.message.text + "\n\n✅ Согласовано руководителем.")

        hr_users = await get_users_by_role("hr")
        text = (f"Согласовано руководителем. Заявка на отпуск\n"
                f"Сотрудник: {employee.full_name}\n"
                f"Даты: {req.start_date.strftime('%d.%m.%Y')} - {req.end_date.strftime('%d.%m.%Y')}")

        for hr in hr_users:
            if hr.telegram_id:
                await callback.bot.send_message(hr.telegram_id, text, reply_markup=get_approval_keyboard(req_id))

    elif req.status == "manager_approved":
        await update_request_status(req_id, "hr_approved")
        await callback.message.edit_text(callback.message.text + "\n\n✅ Согласовано HR.")

        pdf_path = generate_vacation_pdf(req.id, employee.full_name, req.start_date, req.end_date, req.type)

        if employee.telegram_id:
            await callback.bot.send_message(
                employee.telegram_id,
                "Ваш отпуск согласован. Ожидайте приглашение в отдел кадрового администрирования для подписания приказа."
            )
            document = FSInputFile(pdf_path)
            await callback.bot.send_document(employee.telegram_id, document)

    await callback.answer()


@router.callback_query(F.data.startswith("reject_"))
async def process_reject_init(callback: types.CallbackQuery, state: FSMContext):
    req_id = int(callback.data.split("_")[1])
    await state.update_data(reject_req_id=req_id, origin_message_id=callback.message.message_id)
    await callback.message.answer("Отказ требует комментария. Введите причину отклонения:")
    await state.set_state(ApprovalState.waiting_for_reject_comment)
    await callback.answer()


@router.message(ApprovalState.waiting_for_reject_comment)
async def process_reject_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    req_id = data['reject_req_id']

    req = await get_request_by_id(req_id)
    employee = await get_user_by_id(req.user_id)

    await update_request_status(req_id, "rejected", hr_comment=message.text)

    if employee.telegram_id:
        await message.bot.send_message(
            employee.telegram_id,
            f"Заявка отклонена.\nКомментарий: {message.text}"
        )

    await message.answer("Заявка отклонена, сотрудник уведомлен.")
    await state.clear()