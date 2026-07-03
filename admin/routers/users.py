# admin/routers/users.py
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select, or_

from admin.templating import templates, ROOT_PATH
from admin.gateway_auth import require_permission
from admin.context import get_sidebar_badges
from db.database import async_session
from db.models import User
from bot.utils.db_api import get_user_by_id, resolve_manager_id, set_user_manager
from bot.utils.constants import COMPANY_STRUCTURE
from bot.utils.validators import clean_text
from bot.services.request_actions import approve_registration, reject_registration, UserNotFound
from admin.telegram_bot import bot
from core.logging_config import action_logger

router = APIRouter()

ROLE_LABELS = {"employee": "Сотрудник", "manager": "Руководитель", "hr": "HR"}


def _user_to_dict(u: User) -> dict:
    return {
        "id": u.id, "full_name": u.full_name, "phone": u.phone, "telegram_id": u.telegram_id,
        "role": u.role, "role_label": ROLE_LABELS.get(u.role, u.role),
        "department": u.department, "position": u.position,
        "manager_id": u.manager_id, "vacation_days_balance": u.vacation_days_balance,
        "is_active": u.is_active, "approval_status": u.approval_status,
        "language": u.language,
    }


@router.get("/admin/users")
async def users_list_page(request: Request, current_user=Depends(require_permission("hr_bot.users.view"))):
    return templates.TemplateResponse(request, "users_list.html", {
        "active_page": "users",
        "current_user": current_user,
        "nav_badges": await get_sidebar_badges(),
        "roles": ROLE_LABELS,
        "departments": COMPANY_STRUCTURE,
    })


@router.get("/api/admin/users")
async def api_users_list(
    search: Optional[str] = None, role: Optional[str] = None,
    department: Optional[str] = None, is_active: Optional[str] = None,
    approval_status: Optional[str] = None,
    current_user=Depends(require_permission("hr_bot.users.view")),
):
    async with async_session() as session:
        stmt = select(User)
        if search:
            like = f"%{search.strip()}%"
            stmt = stmt.where(or_(User.full_name.like(like), User.phone.like(like), User.tg_username.like(like)))
        if role:
            stmt = stmt.where(User.role == role)
        if department:
            stmt = stmt.where(User.department == department)
        if is_active in ("true", "false"):
            stmt = stmt.where(User.is_active == (is_active == "true"))
        if approval_status:
            stmt = stmt.where(User.approval_status == approval_status)
        stmt = stmt.order_by(User.full_name)

        users = (await session.execute(stmt)).scalars().all()

    return {"items": [_user_to_dict(u) for u in users]}


@router.get("/admin/users/{user_id}")
async def user_detail_page(user_id: int, request: Request, current_user=Depends(require_permission("hr_bot.users.view"))):
    user = await get_user_by_id(user_id)
    if not user:
        return RedirectResponse(url=f"{ROOT_PATH}/admin/users?error=" + "Сотрудник не найден", status_code=302)

    manager = await get_user_by_id(user.manager_id) if user.manager_id else None

    async with async_session() as session:
        managers = (await session.execute(
            select(User).where(User.role.in_(["manager", "hr"])).order_by(User.full_name)
        )).scalars().all()

    return templates.TemplateResponse(request, "users_detail.html", {
        "active_page": "users",
        "current_user": current_user,
        "nav_badges": await get_sidebar_badges(),
        "user": user,
        "manager": manager,
        "managers": managers,
        "roles": ROLE_LABELS,
        "departments": COMPANY_STRUCTURE,
    })


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: Optional[str] = None
    manager_id: Optional[int] = None
    vacation_days_balance: Optional[int] = None
    is_active: Optional[bool] = None


@router.patch("/api/admin/users/{user_id}")
async def api_user_update(user_id: int, payload: UserUpdate, current_user=Depends(require_permission("hr_bot.users.manage"))):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    data = payload.model_dump(exclude_unset=True)

    if "role" in data and data["role"] not in ROLE_LABELS:
        raise HTTPException(status_code=400, detail="Некорректная роль")

    if "manager_id" in data and data["manager_id"]:
        manager = await get_user_by_id(data["manager_id"])
        if not manager or manager.role not in ("manager", "hr"):
            raise HTTPException(status_code=400, detail="Указанный руководитель не найден")

    if "vacation_days_balance" in data and data["vacation_days_balance"] is not None and data["vacation_days_balance"] < 0:
        raise HTTPException(status_code=400, detail="Остаток отпускных дней не может быть отрицательным")

    async with async_session() as session:
        db_user = await session.get(User, user_id)
        for field, value in data.items():
            setattr(db_user, field, value)
        await session.commit()

    action_logger.info("admin_user_updated user_id=%s actor=%s fields=%s", user_id, current_user.username, list(data.keys()))
    return _user_to_dict(await get_user_by_id(user_id))


@router.post("/api/admin/users/{user_id}/approve")
async def api_user_approve(user_id: int, current_user=Depends(require_permission("hr_bot.users.manage"))):
    try:
        user = await approve_registration(bot, user_id, actor=current_user)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    return _user_to_dict(user)


@router.post("/api/admin/users/{user_id}/reject")
async def api_user_reject(user_id: int, current_user=Depends(require_permission("hr_bot.users.manage"))):
    try:
        user = await reject_registration(bot, user_id, actor=current_user)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    return _user_to_dict(user)


@router.post("/api/admin/users/{user_id}/recalculate-manager")
async def api_recalculate_manager(user_id: int, current_user=Depends(require_permission("hr_bot.users.manage"))):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    if not user.department:
        raise HTTPException(status_code=400, detail="У сотрудника не указано подразделение")

    manager_id = await resolve_manager_id(user.department, user.role)
    await set_user_manager(user_id, manager_id)

    action_logger.info(
        "manager_recalculated user_id=%s manager_id=%s actor=%s", user_id, manager_id, current_user.username
    )
    return _user_to_dict(await get_user_by_id(user_id))
