# bot/utils/validators.py
import re
from datetime import date, datetime, timedelta

MAX_COMMENT_LEN = 1000
MAX_NAME_LEN = 100
MAX_CAR_INFO_LEN = 100
MAX_QUESTION_LEN = 2000

_NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁёʼ'`\-. ]+$")


def parse_callback_id(data: str, index: int = -1):
    """Безопасно достаёт числовой id из callback_data вида 'prefix_123'."""
    try:
        return int(data.split("_")[index])
    except (ValueError, IndexError):
        return None


def to_date(value) -> date:
    """Календарь возвращает datetime — приводим к date для БД и сравнений."""
    return value.date() if isinstance(value, datetime) else value


def is_valid_full_name(text: str) -> bool:
    if not text:
        return False
    text = text.strip()
    if not (5 <= len(text) <= MAX_NAME_LEN):
        return False
    if len(text.split()) < 2:
        return False
    return bool(_NAME_RE.match(text))


def is_valid_birth_date(d: date) -> bool:
    today = date.today()
    age = (today - d).days / 365.25
    return 14 <= age <= 100


def is_valid_vacation_start(d: date) -> bool:
    return d >= date.today()


def is_valid_sick_leave_start(d: date) -> bool:
    today = date.today()
    return today - timedelta(days=365) <= d <= today + timedelta(days=30)


def clean_text(text: str, max_len: int = MAX_COMMENT_LEN):
    """Возвращает очищенный текст или None, если ввод пустой/слишком длинный."""
    if not text:
        return None
    text = text.strip()
    if not text or len(text) > max_len:
        return None
    return text
