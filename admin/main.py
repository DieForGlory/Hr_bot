# admin/main.py
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from core.config import ADMIN_SESSION_SECRET
from core.logging_config import setup_logging
from admin.security import install_auth_redirect_handler
from admin.routers import auth, dashboard, users, requests as requests_router, templates_admin, faq, calendar

setup_logging()
logger = logging.getLogger(__name__)

if ADMIN_SESSION_SECRET == "dev-only-insecure-key-change-me":
    logger.warning(
        "ADMIN_SESSION_SECRET не задан в .env — используется небезопасный ключ по умолчанию. "
        "Установите ADMIN_SESSION_SECRET перед выкладкой в прод."
    )

app = FastAPI(title="HR Bot Admin")

app.add_middleware(
    SessionMiddleware,
    secret_key=ADMIN_SESSION_SECRET,
    session_cookie="hr_admin_session",
    same_site="lax",
    max_age=60 * 60 * 12,
)

app.mount("/admin/static", StaticFiles(directory="admin/static"), name="admin_static")

install_auth_redirect_handler(app)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(users.router)
app.include_router(requests_router.router)
app.include_router(templates_admin.router)
app.include_router(faq.router)
app.include_router(calendar.router)
