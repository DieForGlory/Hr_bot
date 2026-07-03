# admin/routers/dashboard.py
import os
from collections import deque
from fastapi import APIRouter, Request, Depends
from sqlalchemy import func, select

from admin.templating import templates
from admin.gateway_auth import require_permission
from admin.context import get_sidebar_badges
from db.database import async_session
from db.models import User, Request as HRRequest
from core.logging_config import LOG_FILE

router = APIRouter()


ACTION_LOGGER_NAME = "hr_bot.actions"
# Файл лога общий для всего процесса (в т.ч. служебных логов aiogram/uvicorn),
# поэтому читаем солидный хвост и уже потом отбираем только записи бизнес-действий.
LOG_TAIL_SCAN_LINES = 2000


def _read_last_log_lines(n: int = 20):
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            raw_lines = deque(f, maxlen=LOG_TAIL_SCAN_LINES)
    except OSError:
        return []

    entries = []
    for line in raw_lines:
        parts = line.rstrip("\n").split(" | ", 3)
        if len(parts) == 4 and parts[2] == ACTION_LOGGER_NAME:
            entries.append({"time": parts[0], "level": parts[1], "logger": parts[2], "message": parts[3]})

    entries = entries[-n:]
    entries.reverse()
    return entries


@router.get("/admin")
async def dashboard_page(request: Request, current_user=Depends(require_permission("hr_bot.dashboard.view"))):
    async with async_session() as session:
        pending_users = (await session.execute(
            select(func.count(User.id)).where(User.approval_status == "pending")
        )).scalar_one()

        active_users = (await session.execute(
            select(func.count(User.id)).where(User.is_active == True)  # noqa: E712
        )).scalar_one()

        pending_manager = (await session.execute(
            select(func.count(HRRequest.id)).where(
                HRRequest.type.like("vacation%"), HRRequest.status == "pending"
            )
        )).scalar_one()

        pending_hr = (await session.execute(
            select(func.count(HRRequest.id)).where(
                HRRequest.type.like("vacation%"), HRRequest.status == "manager_approved"
            )
        )).scalar_one()

        certs_pending = (await session.execute(
            select(func.count(HRRequest.id)).where(
                HRRequest.type.in_(["income_cert", "work_cert"]), HRRequest.status == "pending"
            )
        )).scalar_one()

        certs_in_progress = (await session.execute(
            select(func.count(HRRequest.id)).where(
                HRRequest.type.in_(["income_cert", "work_cert"]), HRRequest.status == "in_progress"
            )
        )).scalar_one()

        sick_without_doc = (await session.execute(
            select(func.count(HRRequest.id)).where(
                HRRequest.type == "sick_leave", HRRequest.file_path.is_(None)
            )
        )).scalar_one()

    stats = [
        {"label": "Новые регистрации", "value": pending_users, "variant": "warn" if pending_users else ""},
        {"label": "Отпуска: у руководителя", "value": pending_manager, "variant": "warn" if pending_manager else ""},
        {"label": "Отпуска: у HR", "value": pending_hr, "variant": "warn" if pending_hr else ""},
        {"label": "Справки: не приняты", "value": certs_pending, "variant": "warn" if certs_pending else ""},
        {"label": "Справки: в работе", "value": certs_in_progress, "variant": ""},
        {"label": "Больничные без документа", "value": sick_without_doc, "variant": "danger" if sick_without_doc else ""},
        {"label": "Активные сотрудники", "value": active_users, "variant": ""},
    ]

    return templates.TemplateResponse(request, "dashboard.html", {
        "active_page": "dashboard",
        "current_user": current_user,
        "nav_badges": await get_sidebar_badges(),
        "stats": stats,
        "log_entries": _read_last_log_lines(20),
    })
