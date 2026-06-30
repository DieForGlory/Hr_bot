from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_approval_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Согласовать", callback_data=f"approve_{request_id}")],
        [InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{request_id}")],
        [InlineKeyboardButton(text="Комментарий", callback_data=f"comment_{request_id}")]
    ])