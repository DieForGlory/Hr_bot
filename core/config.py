
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_SESSION_SECRET = os.getenv("ADMIN_SESSION_SECRET", "dev-only-insecure-key-change-me")