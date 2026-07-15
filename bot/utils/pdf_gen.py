# bot/utils/pdf_gen.py
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from sqlalchemy.future import select
from db.database import async_session
from db.models import DocumentTemplate
from bot.utils.constants import DEFAULT_VACATION_ORDER_TEMPLATE
from bot.utils.org_hierarchy import get_level_breakdown, is_known_department, display_name
from bot.utils.status_labels import get_type_label
from bot.utils.db_api import get_user_by_id
from core.logging_config import action_logger


async def get_template(template_name: str):
    async with async_session() as session:
        result = await session.execute(select(DocumentTemplate).where(DocumentTemplate.name == template_name))
        return result.scalars().first()


def _fmt_date(value, fmt="%d.%m.%Y") -> str:
    try:
        return value.strftime(fmt)
    except Exception:
        return "-"


async def generate_vacation_pdf(req, employee) -> str:
    """Формирует PDF-заявление на отпуск с полной информацией о сотруднике и
    статусами согласования (п.2 ТЗ). req — объект Request, employee — объект User."""
    pdf = FPDF()
    pdf.add_page()

    font_path = "assets/fonts/DejaVuSans.ttf"
    has_unicode_font = os.path.exists(font_path)
    if has_unicode_font:
        pdf.add_font("DejaVu", "", font_path)
        pdf.set_font("DejaVu", size=12)
    else:
        pdf.set_font("Arial", size=12)

    department = employee.department

    # --- Шапка: редактируемый шаблон приказа ---
    template = await get_template("Отпуск")
    content = None
    if template:
        if template.content and template.content.strip():
            content = template.content
        elif template.file_path and os.path.exists(template.file_path):
            with open(template.file_path, "r", encoding="utf-8") as f:
                content = f.read()
    if not content:
        content = DEFAULT_VACATION_ORDER_TEMPLATE

    vacation_type_str = get_type_label(req.type, "ru")
    params = dict(
        full_name=employee.full_name,
        department=department or "-",
        v_type=vacation_type_str,
        start_date=_fmt_date(req.start_date),
        end_date=_fmt_date(req.end_date),
        days_count=req.days_count if req.days_count is not None else "-",
        position=employee.position or "-",
    )
    try:
        formatted_content = content.format(**params)
    except (KeyError, IndexError, ValueError):
        action_logger.warning("vacation_pdf_template_invalid req_id=%s, falling back to default", req.id)
        formatted_content = DEFAULT_VACATION_ORDER_TEMPLATE.format(**params)

    for line in formatted_content.split('\n'):
        pdf.multi_cell(0, 8, text=line, align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def section_title(title: str):
        pdf.ln(3)
        pdf.multi_cell(0, 8, text=title, align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def field(label: str, value: str):
        pdf.multi_cell(0, 7, text=f"{label}: {value}", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # --- Сведения о сотруднике ---
    section_title("Сведения о сотруднике")
    field("ФИО", employee.full_name or "-")
    field("Должность", employee.position or "-")

    if department and is_known_department(department):
        for level_type, level_name in get_level_breakdown(department):
            field(level_type, level_name)
    elif department:
        field("Подразделение", display_name(department))
    else:
        field("Подразделение", "-")

    # --- Параметры заявления ---
    section_title("Заявление на отпуск")
    field("Тип отпуска", vacation_type_str)
    field("Дата подачи заявления", _fmt_date(req.created_at, "%d.%m.%Y %H:%M"))
    field("Период отпуска", f"{_fmt_date(req.start_date)} — {_fmt_date(req.end_date)}")
    field("Количество дней", str(req.days_count) if req.days_count is not None else "-")

    # --- Статусы согласования ---
    section_title("Согласование")
    # Этап руководителя. Согласующего берём из заявки (кто фактически решил);
    # если не зафиксирован (старые заявки) — показываем текущего руководителя.
    manager = await get_user_by_id(employee.manager_id) if employee.manager_id else None
    manager_name = req.manager_approver or (manager.full_name if manager else "-")

    if req.status == "rejected" and req.manager_decided_at and not req.hr_decided_at:
        manager_status = "Отклонено"
    elif req.manager_decided_at:
        manager_status = "Согласовано"
    else:
        manager_status = "Ожидает"
    field("Этап 1 — Руководитель", f"{manager_status} — {_fmt_date(req.manager_decided_at, '%d.%m.%Y %H:%M')}")
    field("  Согласующий", manager_name)
    if req.manager_comment:
        field("  Комментарий", req.manager_comment)

    # Этап HR
    if req.status == "rejected" and req.hr_decided_at:
        hr_status = "Отклонено"
    elif req.status in ("hr_approved", "done") or req.hr_decided_at:
        hr_status = "Согласовано"
    else:
        hr_status = "Ожидает"
    field("Этап 2 — HR", f"{hr_status} — {_fmt_date(req.hr_decided_at, '%d.%m.%Y %H:%M')}")
    field("  Согласующий", req.hr_approver or "-")
    if req.hr_comment:
        field("  Комментарий", req.hr_comment)

    os.makedirs("data/pdfs", exist_ok=True)
    file_path = f"data/pdfs/vacation_order_{req.id}.pdf"
    pdf.output(file_path)

    return file_path
