# bot/utils/pdf_gen.py
import os
from fpdf import FPDF


def generate_vacation_pdf(req_id: int, full_name: str, start_date, end_date, v_type: str) -> str:
    pdf = FPDF()
    pdf.add_page()

    font_path = "assets/fonts/DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", size=14)
    else:
        pdf.set_font("Arial", size=14)

    pdf.cell(200, 10, txt="ПРИКАЗ О ПРЕДОСТАВЛЕНИИ ОТПУСКА", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Сотрудник: {full_name}", ln=True)

    vacation_type_str = "Ежегодный оплачиваемый" if v_type == "vacation_paid" else "Без сохранения заработной платы"
    pdf.cell(200, 10, txt=f"Тип отпуска: {vacation_type_str}", ln=True)
    pdf.cell(200, 10, txt=f"Период: с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}", ln=True)
    pdf.ln(20)
    pdf.cell(200, 10, txt="Подпись руководителя: ________________", ln=True)
    pdf.cell(200, 10, txt="Подпись сотрудника: ________________", ln=True)

    os.makedirs("data/pdfs", exist_ok=True)
    file_path = f"data/pdfs/vacation_order_{req_id}.pdf"
    pdf.output(file_path)

    return file_path