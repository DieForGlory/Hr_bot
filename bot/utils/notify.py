# bot/utils/notify.py
from core.logging_config import action_logger


async def safe_notify(coro, context: str = ""):
    """Отправка Telegram-уведомления не должна валить всё действие (согласование,
    смену статуса и т.д.), если доставка не удалась (бот заблокирован, чат не найден и т.п.)."""
    try:
        return await coro
    except Exception as e:
        action_logger.warning("notify_failed context=%s error=%s", context, e)
        return None
