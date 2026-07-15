# bot/services/request_actions.py
"""
Общая бизнес-логика согласования заявок/регистраций/справок.
Используется и Telegram-хендлерами (bot/handlers/*), и веб-админкой (admin/routers/*),
чтобы действие "согласовать/отклонить/сменить статус" не дублировалось в двух местах.
"""
from aiogram.types import FSInputFile, BufferedInputFile

from bot.utils.db_api import (
    get_request_by_id, update_request_status, get_user_by_id, update_user_approval,
    resolve_manager_id, set_user_manager, next_working_day,
)
from bot.utils.pdf_gen import generate_vacation_pdf
from bot.utils.routing import notify_hr_vacation_approved, send_vacation_statement_to_hr
from bot.utils.notify import safe_notify
from bot.locales.texts import get_text
from core.logging_config import action_logger


class RequestNotFound(Exception):
    pass


class UserNotFound(Exception):
    pass


class CommentRequired(Exception):
    pass


class InvalidTransition(Exception):
    pass


def _actor_label(actor) -> str:
    if actor is None:
        return "-"
    login = getattr(actor, "login", None)
    return f"{actor.full_name} ({login})" if login else actor.full_name


async def _send_attachment(bot, chat_id: int, attachment: dict):
    kind = attachment.get("kind", "document")
    if "file_id" in attachment:
        file = attachment["file_id"]
    else:
        file = BufferedInputFile(attachment["bytes"], filename=attachment.get("filename", "attachment.pdf"))

    if kind == "photo":
        await bot.send_photo(chat_id, file)
    else:
        await bot.send_document(chat_id, file)


async def approve_registration(bot, user_id: int, actor=None) -> "User":
    user = await get_user_by_id(user_id)
    if not user:
        raise UserNotFound()

    await update_user_approval(user_id, "approved")

    # Автоподбор руководителя по оргструктуре (bot/utils/org_hierarchy.py) — только если
    # руководитель ещё не назначен вручную. Если по структуре его найти не удалось
    # (например, руководитель нужного уровня сам ещё не зарегистрирован), поле остаётся
    # пустым — HR всегда может назначить его вручную или позже нажать "Пересчитать" в админке.
    if user.department is not None and user.manager_id is None:
        manager_id = await resolve_manager_id(user.department, user.role)
        if manager_id:
            await set_user_manager(user_id, manager_id)
            action_logger.info("manager_auto_assigned user_id=%s manager_id=%s", user_id, manager_id)

    if user.telegram_id:
        from bot.handlers.main_menu import get_main_keyboard
        await safe_notify(bot.send_message(
            user.telegram_id,
            get_text("reg_account_confirmed", user.language),
            reply_markup=get_main_keyboard(user.language)
        ), context=f"registration_approved user_id={user_id}")

    action_logger.info("registration_approved user_id=%s actor=%s", user_id, _actor_label(actor))
    return await get_user_by_id(user_id)


async def reject_registration(bot, user_id: int, actor=None) -> "User":
    user = await get_user_by_id(user_id)
    if not user:
        raise UserNotFound()

    await update_user_approval(user_id, "rejected")

    if user.telegram_id:
        await safe_notify(
            bot.send_message(user.telegram_id, get_text("reg_account_rejected", user.language)),
            context=f"registration_rejected user_id={user_id}"
        )

    action_logger.info("registration_rejected user_id=%s actor=%s", user_id, _actor_label(actor))
    return await get_user_by_id(user_id)


async def approve_request(bot, req_id: int, actor=None, comment: str = None):
    """Согласование заявки на отпуск: определяет стадию (руководитель/HR) по текущему статусу.
    Возвращает (request, stage), где stage — "manager" или "hr" (какая стадия только что прошла)."""
    req = await get_request_by_id(req_id)
    if not req:
        raise RequestNotFound()
    employee = await get_user_by_id(req.user_id)
    if not employee:
        raise UserNotFound()

    if req.status == "pending":
        await update_request_status(req_id, "manager_approved", manager_comment=comment,
                                    actor_name=_actor_label(actor) if actor else None)
        req = await get_request_by_id(req_id)
        action_logger.info("request_manager_approved req_id=%s actor=%s", req_id, _actor_label(actor))

        await safe_notify(notify_hr_vacation_approved(bot, employee, req), context=f"notify_hr req_id={req_id}")
        return req, "manager"

    elif req.status == "manager_approved":
        await update_request_status(req_id, "hr_approved", hr_comment=comment,
                                    actor_name=_actor_label(actor) if actor else None)
        req = await get_request_by_id(req_id)
        action_logger.info("request_hr_approved req_id=%s actor=%s", req_id, _actor_label(actor))

        pdf_path = await generate_vacation_pdf(req, employee)

        # Дата выхода = первый РАБОЧИЙ день после последнего дня отпуска (п.1 ТЗ):
        # если отпуск кончается в пятницу или перед праздником, выход позже.
        return_date = (await next_working_day(req.end_date)).strftime('%d.%m.%Y') if req.end_date else "-"

        if employee.telegram_id:
            await safe_notify(bot.send_message(
                employee.telegram_id,
                get_text("vacation_approved_final", employee.language).format(return_date=return_date)
            ), context=f"vacation_approved_final req_id={req_id}")
            document = FSInputFile(pdf_path)
            await safe_notify(bot.send_document(employee.telegram_id, document), context=f"vacation_pdf req_id={req_id}")

        # Дубликат заявления администраторам (HR) — нужен для оформления приказа
        await safe_notify(
            send_vacation_statement_to_hr(bot, employee, req, pdf_path, return_date),
            context=f"statement_to_hr req_id={req_id}"
        )
        return req, "hr"

    raise InvalidTransition(f"cannot approve request in status={req.status}")


async def reject_request(bot, req_id: int, actor=None, comment: str = None):
    if not comment or not comment.strip():
        raise CommentRequired()

    req = await get_request_by_id(req_id)
    if not req:
        raise RequestNotFound()
    employee = await get_user_by_id(req.user_id)

    await update_request_status(req_id, "rejected", hr_comment=comment,
                                actor_name=_actor_label(actor) if actor else None)
    action_logger.info("request_rejected req_id=%s actor=%s", req_id, _actor_label(actor))

    if employee and employee.telegram_id:
        lang = employee.language
        await safe_notify(bot.send_message(
            employee.telegram_id,
            f"{get_text('vacation_rejected', lang)}\n{get_text('comment_label', lang)}: {comment}"
        ), context=f"request_rejected req_id={req_id}")

    return await get_request_by_id(req_id)


CERT_STATUSES = ("in_progress", "done", "rejected")


async def set_cert_status(bot, req_id: int, status: str, actor=None, comment: str = None):
    """Смена статуса заявки на справку (accounting/HR). Для 'done' уведомление о готовности
    отправляется ОТДЕЛЬНО через send_cert_ready_notice — на момент смены статуса вложение/место
    получения может быть ещё не собрано (двухшаговый сценарий в Telegram)."""
    if status not in CERT_STATUSES:
        raise ValueError(f"invalid cert status: {status}")
    if status == "rejected" and (not comment or not comment.strip()):
        raise CommentRequired()

    req = await get_request_by_id(req_id)
    if not req:
        raise RequestNotFound()
    employee = await get_user_by_id(req.user_id)

    await update_request_status(req_id, status, hr_comment=comment if status == "rejected" else None)
    action_logger.info("cert_status_change req_id=%s status=%s actor=%s", req_id, status, _actor_label(actor))

    if employee and employee.telegram_id:
        lang = employee.language
        if status == "in_progress":
            await safe_notify(
                bot.send_message(employee.telegram_id, get_text("cert_progress_notice", lang)),
                context=f"cert_in_progress req_id={req_id}"
            )
        elif status == "rejected":
            await safe_notify(bot.send_message(
                employee.telegram_id,
                f"{get_text('cert_rejected_notice_prefix', lang)}\n{get_text('comment_label', lang)}: {comment}"
            ), context=f"cert_rejected req_id={req_id}")

    return await get_request_by_id(req_id)


async def send_cert_ready_notice(bot, req_id: int, actor=None, attachment: dict = None, pickup_note: str = None):
    """Отправляет сотруднику 'Ваша справка готова' + опциональное вложение/место получения."""
    req = await get_request_by_id(req_id)
    if not req:
        raise RequestNotFound()
    employee = await get_user_by_id(req.user_id)
    if not employee:
        raise UserNotFound()

    if employee.telegram_id:
        await safe_notify(
            bot.send_message(employee.telegram_id, get_text("cert_ready", employee.language)),
            context=f"cert_ready req_id={req_id}"
        )

        if attachment:
            await safe_notify(_send_attachment(bot, employee.telegram_id, attachment), context=f"cert_attachment req_id={req_id}")
        elif pickup_note:
            await safe_notify(
                bot.send_message(
                    employee.telegram_id,
                    f"{get_text('cert_pickup_location_label', employee.language)}: {pickup_note[:1000]}"
                ),
                context=f"cert_pickup_note req_id={req_id}"
            )

    action_logger.info("cert_ready_notice_sent req_id=%s actor=%s", req_id, _actor_label(actor))
    return req
