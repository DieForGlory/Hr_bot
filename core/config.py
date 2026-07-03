
import os
from dotenv import load_dotenv

try:
    load_dotenv()
except Exception:
    # В контейнере переменные приходят из compose; битый .env не должен ронять запуск.
    pass

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_SESSION_SECRET = os.getenv("ADMIN_SESSION_SECRET", "dev-only-insecure-key-change-me")