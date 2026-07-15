# admin/routers/requests.py
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select, and_

from admin.templating import templates, ROOT_PATH
from admin.gateway_auth import require_permission
from admin.context import get_sidebar_badges
from admin.telegram_bot import bot
from db.database import async_session
from db.models import Request as HRRequest, User
from bot.utils.db_api import get_request_by_id, get_user_by_id
from bot.utils.status_labels import get_status_label, get_type_label, TYPE_LABELS
from bot.utils.validators import clean_text, MAX_COMMENT_LEN
from bot.utils.constants import VACATION_TYPES
from bot.services.request_actions import (
    approve_request, reject_request, set_cert_status, send_cert_ready_notice,
    RequestNotFound, UserNotFound, CommentRequired, InvalidTransition,
)
from core.logging_config import action_logger

router = APIRouter()

CERT_TYPES = ("income_cert", "work_cert")
VACATION_LIKE_TYPES = tuple(VACATION_TYPES)


def _request_to_dict(r: HRRequest, employee: Optional[User] = None) -> dict:
    return {
        "id": r.id, "user_id": r.user_id,
        "employee_name": employee.full_name if employee else None,
        "type": r.type, "type_label": get_type_label(r.type),
        "status": r.status, "status_label": get_status_label(r.type, r.status),
        "start_date": r.start_date.isoformat() if r.start_date else None,
        "end_date": r.end_date.isoformat() if r.end_date else None,
        "days_count": r.days_count,
        "comment": r.comment, "hr_comment": r.hr_comment, "manager_comment": r.manager_comment,
        "manager_decided_at": r.manager_decided_at.isoformat() if r.manager_decided_at else None,
        "hr_decided_at": r.hr_decided_at.isoformat() if r.hr_decided_at else None,
        "has_file": bool(r.file_path),
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "is_cert": r.type in CERT_TYPES,
        "is_vacation": r.type in VACATION_LIKE_TYPES,
    }


@router.get("/admin/requests")
async def requests_list_page(request: Request, current_user=Depends(require_permission("hr_bot.requests.view"))):
    return templates.TemplateResponse(request, "requests_list.html", {
        "active_page": "requests",
        "current_user": current_user,
        "nav_badges": await get_sidebar_badges(),
        "type_labels": TYPE_LABELS,
    })


@router.get("/api/admin/requests")
async def api_requests_list(
    type: Optional[str] = None, status: Optional[str] = None, user_id: Optional[int] = None,
    employee_search: Optional[str] = None,
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    current_user=Depends(require_permission("hr_bot.requests.view")),
):
    async with async_session() as session:
        stmt = select(HRRequest, User).join(User, HRRequest.user_id == User.id)
        conditions = []
        if type:
            conditions.append(HRRequest.type == type)
        if status:
            conditions.append(HRRequest.status == status)
        if user_id:
            conditions.append(HRRequest.user_id == user_id)
        if employee_search:
            conditions.append(User.full_name.like(f"%{employee_search.strip()}%"))
        if date_from:
            conditions.append(HRRequest.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            conditions.append(HRRequest.created_at <= datetime.fromisoformat(date_to + "T23:59:59"))
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(HRRequest.created_at.desc())

        rows = (await session.execute(stmt)).all()

    return {"items": [_request_to_dict(r, u) for r, u in rows]}


@router.get("/admin/requests/{req_id}")
async def request_detail_page(req_id: int, request: Request, current_user=Depends(require_permission("hr_bot.requests.view"))):
    req = await get_request_by_id(req_id)
    if not req:
        return RedirectResponse(url=f"{ROOT_PATH}/admin/requests?error=Заявка+не+найдена", status_code=302)
    employee = await get_user_by_id(req.user_id)
    manager = await get_user_by_id(employee.manager_id) if employee and employee.manager_id else None

    return templates.TemplateResponse(request, "requests_detail.html", {
        "active_page": "requests",
        "current_user": current_user,
        "nav_badges": await get_sidebar_badges(),
        "req": req,
        "employee": employee,
        "manager": manager,
        "status_label": get_status_label(req.type, req.status),
        "type_label": get_type_label(req.type),
        "is_cert": req.type in CERT_TYPES,
        "is_vacation": req.type in VACATION_LIKE_TYPES,
    })


@router.get("/api/admin/requests/{req_id}")
async def api_request_detail(req_id: int, current_user=Depends(require_permission("hr_bot.requests.view"))):
    req = await get_request_by_id(req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    employee = await get_user_by_id(req.user_id)
    return _request_to_dict(req, employee)


class ApproveBody(BaseModel):
    comment: Optional[str] = None


class ReasonBody(BaseModel):
    comment: str


@router.post("/api/admin/requests/{req_id}/approve")
async def api_request_approve(req_id: int, payload: ApproveBody, current_user=Depends(require_permission("hr_bot.requests.manage"))):
    req = await get_request_by_id(req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if req.type not in VACATION_LIKE_TYPES:
        raise HTTPException(status_code=400, detail="Это действие доступно только для заявок на отпуск")
    if req.status == "pending":
        raise HTTPException(
            status_code=403,
            detail="Заявка ожидает решения руководителя — согласовать её на этом этапе может только руководитель в Telegram"
        )

    comment = clean_text(payload.comment, MAX_COMMENT_LEN) if payload.comment else None
    try:
        req, stage = await approve_request(bot, req_id, actor=current_user, comment=comment)
    except RequestNotFound:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    except UserNotFound:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    except InvalidTransition:
        raise HTTPException(status_code=409, detail="Заявка уже обработана")

    employee = await get_user_by_id(req.user_id)
    return _request_to_dict(req, employee)


@router.post("/api/admin/requests/{req_id}/reject")
async def api_request_reject(req_id: int, payload: ReasonBody, current_user=Depends(require_permission("hr_bot.requests.manage"))):
    req = await get_request_by_id(req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if req.type not in VACATION_LIKE_TYPES:
        raise HTTPException(status_code=400, detail="Это действие доступно только для заявок на отпуск")
    if req.status == "pending":
        raise HTTPException(
            status_code=403,
            detail="Заявка ожидает решения руководителя — отклонить её на этом этапе может только руководитель в Telegram"
        )

    comment = clean_text(payload.comment, MAX_COMMENT_LEN)
    if not comment:
        raise HTTPException(status_code=400, detail="Комментарий обязателен при отклонении")

    try:
        req = await reject_request(bot, req_id, actor=current_user, comment=comment)
    except RequestNotFound:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    except CommentRequired:
        raise HTTPException(status_code=400, detail="Комментарий обязателен при отклонении")

    employee = await get_user_by_id(req.user_id)
    return _request_to_dict(req, employee)


@router.post("/api/admin/requests/{req_id}/cert-progress")
async def api_cert_progress(req_id: int, current_user=Depends(require_permission("hr_bot.requests.manage"))):
    req = await get_request_by_id(req_id)
    if not req or req.type not in CERT_TYPES:
        raise HTTPException(status_code=404, detail="Заявка на справку не найдена")

    try:
        req = await set_cert_status(bot, req_id, "in_progress", actor=current_user)
    except RequestNotFound:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    employee = await get_user_by_id(req.user_id)
    return _request_to_dict(req, employee)


@router.post("/api/admin/requests/{req_id}/cert-done")
async def api_cert_done(
    req_id: int,
    pickup_note: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user=Depends(require_permission("hr_bot.requests.manage")),
):
    req = await get_request_by_id(req_id)
    if not req or req.type not in CERT_TYPES:
        raise HTTPException(status_code=404, detail="Заявка на справку не найдена")

    try:
        req = await set_cert_status(bot, req_id, "done", actor=current_user)
    except RequestNotFound:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    attachment = None
    if file is not None and file.filename:
        content = await file.read()
        if content:
            attachment = {"kind": "document", "bytes": content, "filename": file.filename}

    note = clean_text(pickup_note, MAX_COMMENT_LEN) if pickup_note else None

    req = await send_cert_ready_notice(bot, req_id, actor=current_user, attachment=attachment, pickup_note=note)

    employee = await get_user_by_id(req.user_id)
    return _request_to_dict(req, employee)


@router.delete("/api/admin/requests/{req_id}")
async def api_request_delete(req_id: int, current_user=Depends(require_permission("hr_bot.requests.manage"))):
    """Удаление тестовой/ошибочной заявки или зависшего статуса (п.6 ТЗ).
    Удаляется только запись заявки; баланс отпускных при этом не восстанавливается
    автоматически — при необходимости скорректируйте его вручную в карточке сотрудника."""
    async with async_session() as session:
        req = await session.get(HRRequest, req_id)
        if not req:
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        await session.delete(req)
        await session.commit()
    action_logger.info("admin_request_deleted req_id=%s actor=%s", req_id, current_user.username)
    return {"ok": True, "deleted": req_id}


@router.post("/api/admin/requests/{req_id}/cert-reject")
async def api_cert_reject(req_id: int, payload: ReasonBody, current_user=Depends(require_permission("hr_bot.requests.manage"))):
    req = await get_request_by_id(req_id)
    if not req or req.type not in CERT_TYPES:
        raise HTTPException(status_code=404, detail="Заявка на справку не найдена")

    comment = clean_text(payload.comment, MAX_COMMENT_LEN)
    if not comment:
        raise HTTPException(status_code=400, detail="Комментарий обязателен при отклонении")

    try:
        req = await set_cert_status(bot, req_id, "rejected", actor=current_user, comment=comment)
    except RequestNotFound:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    except CommentRequired:
        raise HTTPException(status_code=400, detail="Комментарий обязателен при отклонении")

    employee = await get_user_by_id(req.user_id)
    return _request_to_dict(req, employee)
