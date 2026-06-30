
from aiogram import Bot
from bot.keyboards.inline import get_approval_keyboard
from bot.utils.db_api import get_user_by_id, get_users_by_role


async def notify_manager(bot: Bot, employee, req_id: int, data: dict):
    if not employee.manager_id:
        return
    manager = await get_user_by_id(employee.manager_id)
    if manager and manager.telegram_id:
        text = (f"Заявка на отпуск\n"
                f"ФИО: {employee.full_name}\n"
                f"Тип: {data['vacation_type']}\n"
                f"Даты: {data['start_date'].strftime('%d.%m.%Y')} - {data['end_date'].strftime('%d.%m.%Y')}")
        await bot.send_message(manager.telegram_id, text, reply_markup=get_approval_keyboard(req_id))


async def route_certificate(bot: Bot, req_id: int, cert_type: str, employee, comment: str):
    target_role = "accounting" if cert_type == "Справка о доходах" else "hr"
    target_users = await get_users_by_role(target_role)

    text = (f"Новая заявка на справку: {cert_type}\n"
            f"Сотрудник: {employee.full_name}\n"
            f"Комментарий: {comment}")

    for u in target_users:
        if u.telegram_id:
            await bot.send_message(u.telegram_id, text)