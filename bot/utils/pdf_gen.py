# bot/utils/pdf_gen.py
"""Формирование PDF-заявления на отпуск (п.2 ТЗ).

Формат — по утверждённым образцам (заявление_на_отпуск.docx, Заявление_БС_.docx):
шапка «Кому / От» справа, заголовок «Заявление», текст просьбы по типу отпуска и
блок «Статус согласования» с тремя участниками (работник, непосредственный
руководитель, ответственное лицо ДРП) — с должностями, ФИО, решениями и
комментариями. В блоке «Работник» дополнительно выводятся уровни оргструктуры
(департамент/управление/отдел/группа) — требование п.2 ТЗ.
"""
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from bot.utils.constants import (
    VACATION_STATEMENT_TEXTS, COMPANY_NAME, CEO_ADDRESS_TITLE, CEO_FALLBACK_NAME,
    CEO_POSITION_MATCH, HR_RESPONSIBLE_TITLE,
)
from bot.utils.org_hierarchy import get_level_breakdown, is_known_department, display_name
from bot.utils.status_labels import get_type_label
from bot.utils.db_api import get_user_by_id, get_user_by_full_name, find_user_by_position
from core.logging_config import action_logger


def _fmt_date(value, fmt="%d.%m.%Y") -> str:
    try:
        return value.strftime(fmt)
    except Exception:
        return "-"


def _fmt_days(value) -> str:
    if value is None:
        return "-"
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value)
    return str(int(f)) if f == int(f) else str(round(f, 2))


async def _approver_line(stored_name: str, fallback_user):
    """(ФИО, должность) согласующего: сначала тот, кто реально принял решение."""
    name = stored_name or (fallback_user.full_name if fallback_user else None)
    if not name:
        return "-", "-"
    user = await get_user_by_full_name(name)
    if user is None and fallback_user is not None and name == fallback_user.full_name:
        user = fallback_user
    return name, (user.position if user and user.position else "-")


def _stage_status(decided_at, rejected: bool) -> str:
    if not decided_at:
        return "Ожидает"
    return "Отклонено" if rejected else "Согласовано"


async def generate_vacation_pdf(req, employee) -> str:
    pdf = FPDF()
    pdf.add_page()

    font_path = "assets/fonts/DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path)
        pdf.set_font("DejaVu", size=12)
    else:
        pdf.set_font("Arial", size=12)

    def line(text: str, align: str = "L", h: int = 6):
        pdf.multi_cell(0, h, text=text, align=align, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # --- Шапка: кому / от кого ---
    ceo = await find_user_by_position(CEO_POSITION_MATCH)
    ceo_name = (ceo.full_name if ceo else CEO_FALLBACK_NAME) or "—"
    if not ceo and not CEO_FALLBACK_NAME:
        action_logger.warning("vacation_pdf_ceo_not_found req_id=%s", req.id)

    line(f"Кому: {CEO_ADDRESS_TITLE}", align="R")
    line(COMPANY_NAME, align="R")
    line(ceo_name, align="R")
    line(f"От: {employee.position or '-'}", align="R")
    line(employee.full_name or "-", align="R")

    pdf.ln(8)
    line("Заявление", align="C", h=8)
    pdf.ln(2)

    # --- Текст просьбы (по типу отпуска) ---
    statement = VACATION_STATEMENT_TEXTS.get(req.type)
    if statement:
        body = statement.format(days=_fmt_days(req.days_count), start_date=_fmt_date(req.start_date))
    else:
        # неизвестный тип — нейтральная формулировка, чтобы документ всё равно сформировался
        action_logger.warning("vacation_pdf_unknown_type req_id=%s type=%s", req.id, req.type)
        body = (
            f"Прошу предоставить мне отпуск ({get_type_label(req.type, 'ru')}) продолжительностью "
            f"«{_fmt_days(req.days_count)}» календарных дня — с {_fmt_date(req.start_date)}."
        )
    line(body, align="J")

    pdf.ln(8)
    line("Статус согласования:")
    pdf.ln(2)

    # --- Работник ---
    line("Работник:")
    line(f"   Должность: {employee.position or '-'}")
    line(f"   ФИО: {employee.full_name or '-'}")
    if employee.department and is_known_department(employee.department):
        for level_type, level_name in get_level_breakdown(employee.department):
            line(f"   {level_type}: {level_name}")
    elif employee.department:
        line(f"   Подразделение: {display_name(employee.department)}")
    line(f"   Дата заявки: {_fmt_date(req.created_at, '%d.%m.%Y %H:%M')}")
    line(f"   Комментарий: {req.comment or '-'}")
    pdf.ln(3)

    # --- Непосредственный руководитель ---
    manager = await get_user_by_id(employee.manager_id) if employee.manager_id else None
    mgr_name, mgr_position = await _approver_line(req.manager_approver, manager)
    mgr_rejected = req.status == "rejected" and bool(req.manager_decided_at) and not req.hr_decided_at

    line("Непосредственный руководитель:")
    line(f"   Должность: {mgr_position}")
    line(f"   ФИО: {mgr_name}")
    line(f"   Решение: {_stage_status(req.manager_decided_at, mgr_rejected)}"
         f" ({_fmt_date(req.manager_decided_at, '%d.%m.%Y %H:%M')})")
    line(f"   Комментарий: {req.manager_comment or '-'}")
    pdf.ln(3)

    # --- Ответственное лицо ДРП (HR) ---
    hr_name, hr_position = await _approver_line(req.hr_approver, None)
    hr_rejected = req.status == "rejected" and bool(req.hr_decided_at)

    line(HR_RESPONSIBLE_TITLE)
    line(f"   Должность: {hr_position}")
    line(f"   ФИО: {hr_name}")
    line(f"   Решение: {_stage_status(req.hr_decided_at, hr_rejected)}"
         f" ({_fmt_date(req.hr_decided_at, '%d.%m.%Y %H:%M')})")
    line(f"   Комментарий: {req.hr_comment or '-'}")

    os.makedirs("data/pdfs", exist_ok=True)
    file_path = f"data/pdfs/vacation_statement_{req.id}.pdf"
    pdf.output(file_path)

    return file_path
