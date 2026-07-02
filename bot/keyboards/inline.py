# bot/keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.locales.texts import get_text

def get_approval_keyboard(request_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("approve_button", lang), callback_data=f"approve_{request_id}")],
        [InlineKeyboardButton(text=get_text("reject_button", lang), callback_data=f"reject_{request_id}")],
        [InlineKeyboardButton(text=get_text("comment_button", lang), callback_data=f"comment_{request_id}")]
    ])

def get_vacation_types_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("vacation_type_paid", lang), callback_data="vac_type_paid")],
        [InlineKeyboardButton(text=get_text("vacation_type_unpaid", lang), callback_data="vac_type_unpaid")]
    ])

def get_confirm_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("vacation_confirm_submit", lang), callback_data="confirm_vacation")],
        [InlineKeyboardButton(text=get_text("vacation_confirm_cancel", lang), callback_data="cancel_action")]
    ])

def get_faq_list_kb(faqs) -> InlineKeyboardMarkup:
    kb = []
    for faq in faqs:
        kb.append([InlineKeyboardButton(text=faq.question, callback_data=f"faq_{faq.id}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_faq_back_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("faq_back_button", lang), callback_data="faq_back")]
    ])

def get_cert_status_keyboard(request_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("cert_progress_button", lang), callback_data=f"cert_progress_{request_id}")],
        [InlineKeyboardButton(text=get_text("cert_done_button", lang), callback_data=f"cert_done_{request_id}")],
        [InlineKeyboardButton(text=get_text("reject_button", lang), callback_data=f"cert_reject_{request_id}")]
    ])

def get_calendar_nav_kb(year: int, month: int, lang: str = "ru") -> InlineKeyboardMarkup:
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("calendar_prev_month", lang), callback_data=f"cal_{prev_year}_{prev_month}"),
            InlineKeyboardButton(text=get_text("calendar_next_month", lang), callback_data=f"cal_{next_year}_{next_month}"),
        ]
    ])
