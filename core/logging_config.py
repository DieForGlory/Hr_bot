import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "data/logs"
LOG_FILE = os.path.join(LOG_DIR, "bot.log")


def setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return  # уже настроено в этом процессе — не плодим дублирующиеся хендлеры

    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Библиотеки логируют на INFO каждое обновление/запрос — это шум для журнала
    # действий пользователей (ТЗ: "Логирование действий"). Оставляем только предупреждения/ошибки.
    for noisy_logger in ("aiogram", "aiogram.event", "aiogram.dispatcher", "uvicorn.access"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


action_logger = logging.getLogger("hr_bot.actions")
