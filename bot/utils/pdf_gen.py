# bot/utils/pdf_gen.py
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from sqlalchemy.future import select
from db.database import async_session
from db.models import DocumentTemplate
from bot.utils.constants import DEFAULT_VACATION_ORDER_TEMPLATE
from core.logging_config import action_logger


async def get_template(template_name: str):
    async with async_session() as session:
        result = await session.execute(select(DocumentTemplate).where(DocumentTemplate.name == template_name))
        return result.scalars().first()


async def generate_vacation_pdf(req_id: int, full_name: str, start_date, end_date, v_type: str,
                                 department: str = None, days_count: int = None) -> str:
    pdf = FPDF()
    pdf.add_page()

    font_path = "assets/fonts/DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path)
        pdf.set_font("DejaVu", size=12)
    else:
        pdf.set_font("Arial", size=12)

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

    vacation_type_str = "Ежегодный оплачиваемый" if v_type == "vacation_paid" else "Без сохранения заработной платы"

    params = dict(
        full_name=full_name,
        department=department or "-",
        v_type=vacation_type_str,
        start_date=start_date.strftime('%d.%m.%Y'),
        end_date=end_date.strftime('%d.%m.%Y'),
        days_count=days_count if days_count is not None else "-"
    )

    try:
        formatted_content = content.format(**params)
    except (KeyError, IndexError, ValueError):
        # Шаблон из админки содержит неизвестные/битые плейсхолдеры — используем встроенный
        action_logger.warning("vacation_pdf_template_invalid req_id=%s, falling back to default", req_id)
        formatted_content = DEFAULT_VACATION_ORDER_TEMPLATE.format(**params)

    for line in formatted_content.split('\n'):
        pdf.multi_cell(0, 10, text=line, align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    os.makedirs("data/pdfs", exist_ok=True)
    file_path = f"data/pdfs/vacation_order_{req_id}.pdf"
    pdf.output(file_path)

    return file_path
