# admin/routers/auth.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from admin.templating import templates
from admin.security import verify_password, resolve_admin_user
from bot.utils.db_api import get_user_by_login
from core.logging_config import action_logger

router = APIRouter()


@router.get("/admin/login")
async def login_page(request: Request):
    if await resolve_admin_user(request):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/admin/login")
async def login_submit(request: Request, login: str = Form(...), password: str = Form(...)):
    user = await get_user_by_login(login.strip())

    if not user or not verify_password(password, user.password_hash):
        action_logger.info("admin_login_failed login=%s", login.strip())
        return templates.TemplateResponse(
            request, "login.html", {"error": "Неверный логин или пароль."}, status_code=401
        )

    if user.role != "hr" or not user.is_active:
        action_logger.info("admin_login_denied login=%s user_id=%s", login.strip(), user.id)
        return templates.TemplateResponse(
            request, "login.html", {"error": "Доступ в админку для этой учётной записи закрыт."}, status_code=403
        )

    request.session["user_id"] = user.id
    action_logger.info("admin_login_success user_id=%s login=%s", user.id, user.login)
    return RedirectResponse(url="/admin", status_code=302)


@router.post("/admin/logout")
async def logout(request: Request):
    user_id = request.session.get("user_id")
    request.session.clear()
    if user_id:
        action_logger.info("admin_logout user_id=%s", user_id)
    return RedirectResponse(url="/admin/login", status_code=302)
