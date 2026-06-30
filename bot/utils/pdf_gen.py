# bot/utils/pdf_gen.py
import os
from fpdf import FPDF
from sqlalchemy.future import select
from db.database import async_session
from db.models import DocumentTemplate


async def get_template_path(template_name: str) -> str:
    async with async_session() as session:
        result = await session.execute(select(DocumentTemplate).where(DocumentTemplate.name == template_name))
        template = result.scalars().first()
        return template.file_path if template else None


async def generate_vacation_pdf(req_id: int, full_name: str, start_date, end_date, v_type: str) -> str:
    pdf = FPDF()
    pdf.add_page()

    font_path = "assets/fonts/DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", size=12)
    else:
        pdf.set_font("Arial", size=12)

    template_path = await get_template_path("Отпуск")

    if template_path and os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = (
            "ПРИКАЗ О ПРЕДОСТАВЛЕНИИ ОТПУСКА\n\n"
            "Сотрудник: {full_name}\n"
            "Тип отпуска: {v_type}\n"
            "Период: с {start_date} по {end_date}\n\n"
            "Подпись руководителя: ________________\n"
            "Подпись сотрудника: ________________"
        )

    vacation_type_str = "Ежегодный оплачиваемый" if v_type == "vacation_paid" else "Без сохранения заработной платы"

    formatted_content = content.format(
        full_name=full_name,
        v_type=vacation_type_str,
        start_date=start_date.strftime('%d.%m.%Y'),
        end_date=end_date.strftime('%d.%m.%Y')
    )

    for line in formatted_content.split('\n'):
        pdf.multi_cell(0, 10, txt=line, align='L')

    os.makedirs("data/pdfs", exist_ok=True)
    file_path = f"data/pdfs/vacation_order_{req_id}.pdf"
    pdf.output(file_path)

    return file_path