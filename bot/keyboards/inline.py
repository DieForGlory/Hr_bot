# bot/keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_approval_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Согласовать", callback_data=f"approve_{request_id}")],
        [InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{request_id}")],
        [InlineKeyboardButton(text="Комментарий", callback_data=f"comment_{request_id}")]
    ])

def get_vacation_types_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ежегодный оплачиваемый отпуск", callback_data="vac_type_paid")],
        [InlineKeyboardButton(text="Отпуск без содержания", callback_data="vac_type_unpaid")]
    ])

def get_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отправить заявку", callback_data="confirm_vacation")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_action")]
    ])

def get_faq_list_kb(faqs) -> InlineKeyboardMarkup:
    kb = []
    for faq in faqs:
        kb.append([InlineKeyboardButton(text=faq.question, callback_data=f"faq_{faq.id}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_faq_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад к списку вопросов", callback_data="faq_back")]
    ])

def get_cert_status_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="В работу", callback_data=f"cert_progress_{request_id}")],
        [InlineKeyboardButton(text="Готово", callback_data=f"cert_done_{request_id}")],
        [InlineKeyboardButton(text="Отклонить", callback_data=f"cert_reject_{request_id}")]
    ])

def get_faq_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Аванс и ЗП", callback_data="faq_salary")],
        [InlineKeyboardButton(text="Отпускные", callback_data="faq_vacation")],
        [InlineKeyboardButton(text="Больничные", callback_data="faq_sick")],
        [InlineKeyboardButton(text="Персональные документы", callback_data="faq_docs")]
    ])