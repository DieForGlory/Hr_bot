
from aiogram import Bot
from bot.utils.db_api import get_user_by_id, get_users_by_role
from bot.utils.status_labels import get_type_label
from bot.utils.notify_window import dispatch_notification
from bot.locales.texts import get_text


async def send_registration_to_hr(bot, user_id: int, data: dict):
    hr_users = await get_users_by_role("hr")

    for hr in hr_users:
        if not hr.telegram_id:
            continue
        lang = hr.language
        text = get_text("registration_notification_header", lang).format(
            full_name=data['full_name'],
            position=data.get('position') or '-',
            subdivision=data['subdivision'],
            role_text=data['role_text'],
            phone=data['phone'],
            tg_username=data['tg_username'],
            birth_date=data['birth_date'],
            car_info=data['car_info'],
        )
        await dispatch_notification(
            bot, hr.telegram_id, text, lang,
            kb_kind="registration", kb_ref_id=user_id,
            attachment={"kind": "photo", "file_id": data['face_id_photo']},
            context=f"send_registration_to_hr user_id={user_id} hr_id={hr.id}",
        )


def _vacation_type_name(vac_type_key: str, lang: str) -> str:
    # vac_type_key — короткий ключ: paid/unpaid/marriage/childbirth
    return get_text(f"vacation_type_{vac_type_key}", lang)


async def notify_manager(bot: Bot, employee, req_id: int, data: dict, document_file_id: str = None):
    if not employee.manager_id:
        return
    manager = await get_user_by_id(employee.manager_id)
    if manager and manager.telegram_id:
        lang = manager.language
        vac_type_name = _vacation_type_name(data['vacation_type'], lang)
        text = get_text("vacation_request_notification", lang).format(
            full_name=employee.full_name,
            department=employee.department or '-',
            v_type=vac_type_name,
            start=data['start_date'].strftime('%d.%m.%Y'),
            end=data['end_date'].strftime('%d.%m.%Y'),
            days=data['days_count'],
        )
        attachment = {"kind": "document", "file_id": document_file_id} if document_file_id else None
        await dispatch_notification(
            bot, manager.telegram_id, text, lang,
            kb_kind="approval", kb_ref_id=req_id, attachment=attachment,
            context=f"notify_manager req_id={req_id}",
        )


async def notify_hr_vacation_approved(bot: Bot, employee, req):
    hr_users = await get_users_by_role("hr")
    vac_type_key = req.type.replace("vacation_", "")

    for hr in hr_users:
        if not hr.telegram_id:
            continue
        lang = hr.language
        vac_type_name = _vacation_type_name(vac_type_key, lang)
        text = get_text("vacation_hr_notification", lang).format(
            full_name=employee.full_name,
            department=employee.department or '-',
            v_type=vac_type_name,
            start=req.start_date.strftime('%d.%m.%Y'),
            end=req.end_date.strftime('%d.%m.%Y'),
            comment=req.manager_comment or '-',
        )
        attachment = {"kind": "document", "file_id": req.file_path} if req.file_path else None
        await dispatch_notification(
            bot, hr.telegram_id, text, lang,
            kb_kind="approval", kb_ref_id=req.id, attachment=attachment,
            context=f"notify_hr_vacation_approved req_id={req.id} hr_id={hr.id}",
        )


async def send_vacation_statement_to_hr(bot: Bot, employee, req, pdf_path: str, return_date: str = "-"):
    """Дублирует согласованное заявление администраторам (HR) — оно нужно им для
    оформления приказа. Отправляется по тому же рабочему окну, что и остальные
    уведомления админам (п.5)."""
    hr_users = await get_users_by_role("hr")
    vac_type_key = req.type.replace("vacation_", "")

    for hr in hr_users:
        if not hr.telegram_id:
            continue
        lang = hr.language
        text = get_text("vacation_statement_for_hr", lang).format(
            full_name=employee.full_name,
            position=employee.position or '-',
            department=employee.department or '-',
            v_type=_vacation_type_name(vac_type_key, lang),
            start=req.start_date.strftime('%d.%m.%Y') if req.start_date else '-',
            end=req.end_date.strftime('%d.%m.%Y') if req.end_date else '-',
            days=req.days_count if req.days_count is not None else '-',
            return_date=return_date,
        )
        await dispatch_notification(
            bot, hr.telegram_id, text, lang,
            attachment={"kind": "document_path", "file_id": pdf_path},
            context=f"vacation_statement_to_hr req_id={req.id} hr_id={hr.id}",
        )


async def route_certificate(bot: Bot, req_id: int, cert_req_type: str, employee, comment: str):
    """cert_req_type — канонический тип заявки ("income_cert"/"work_cert"), не отображаемый текст."""
    target_role = "accounting" if cert_req_type == "income_cert" else "hr"
    target_users = await get_users_by_role(target_role)

    for u in target_users:
        if not u.telegram_id:
            continue
        lang = u.language
        text = get_text("cert_request_notification", lang).format(
            cert_type=get_type_label(cert_req_type, lang),
            full_name=employee.full_name,
            department=employee.department or '-',
            comment=comment or '-',
        )
        await dispatch_notification(
            bot, u.telegram_id, text, lang,
            kb_kind="cert", kb_ref_id=req_id,
            context=f"route_certificate req_id={req_id} user_id={u.id}",
        )
