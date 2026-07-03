# admin/templating.py
import os

from fastapi.templating import Jinja2Templates

# Префикс, под которым админка живёт за шлюзом (напр. /hr_bot). Локально пусто.
ROOT_PATH = os.getenv("ROOT_PATH", "").rstrip("/")

templates = Jinja2Templates(directory="admin/templates")

# base_path подставляется во все ссылки шаблонов ({{ base_path }}/admin/...),
# чтобы они указывали на /hr_bot/admin/... за шлюзом. Локально (ROOT_PATH="")
# ссылки остаются /admin/... как раньше.
templates.env.globals["base_path"] = ROOT_PATH
