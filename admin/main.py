# admin/main.py
import logging
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.logging_config import setup_logging
from admin.routers import dashboard, users, requests as requests_router, templates_admin, faq, calendar

setup_logging()
logger = logging.getLogger(__name__)

# Префикс за шлюзом (/hr_bot). Локально пусто. Используется и в шаблонах (base_path).
ROOT_PATH = os.getenv("ROOT_PATH", "").rstrip("/")

app = FastAPI(title="HR Bot Admin", root_path=ROOT_PATH)

# Статика админки. Снаружи /hr_bot/admin/static/..., шлюз срезает /hr_bot ->
# /admin/static/... (совпадает с этим mount).
app.mount("/admin/static", StaticFiles(directory="admin/static"), name="admin_static")

app.include_router(dashboard.router)
app.include_router(users.router)
app.include_router(requests_router.router)
app.include_router(templates_admin.router)
app.include_router(faq.router)
app.include_router(calendar.router)


@app.get("/health")
async def health():
    """Публичный health-check (шлюз пробрасывает /hr_bot/health без auth,
    Docker-healthcheck бьёт напрямую)."""
    return {"status": "healthy"}


# --- Регистрация в gateway: service discovery + heartbeat ---
# Только для admin (это HTTP-сервис системы). Non-fatal и опционально:
# включается ENABLE_SERVICE_DISCOVERY=true (в prod-compose). Локально выключено.
if os.getenv("ENABLE_SERVICE_DISCOVERY", "false").lower() in ("1", "true", "yes"):
    try:
        from auth_connector import init_service_discovery_fastapi

        init_service_discovery_fastapi(
            app,
            service_key=os.getenv("SERVICE_KEY", "hr_bot"),
            internal_url=os.getenv("SERVICE_INTERNAL_URL", "http://hr-bot-admin:8000"),
            registry_url=os.getenv("REGISTRY_URL", "http://auth-service:80/api/registry"),
            health_check_path="/health",
            heartbeat_interval=int(os.getenv("HEARTBEAT_INTERVAL", "30")),
            api_key=os.getenv("INTERNAL_API_KEY", ""),
            metadata={"version": "1.0.0"},
        )
        logger.info("Service discovery включён (service_key=hr_bot)")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Service discovery не инициализирован: %s", exc)
