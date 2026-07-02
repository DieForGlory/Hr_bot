# admin/routers/templates_admin.py
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select

from admin.templating import templates
from admin.security import require_admin_page, require_admin_api
from admin.context import get_sidebar_badges
from db.database import async_session
from db.models import DocumentTemplate
from bot.utils.validators import clean_text
from core.logging_config import action_logger

router = APIRouter()

PLACEHOLDER_HINT = "{full_name}, {department}, {v_type}, {start_date}, {end_date}, {days_count}"


def _tpl_to_dict(t: DocumentTemplate) -> dict:
    return {"id": t.id, "name": t.name, "content": t.content, "file_path": t.file_path}


@router.get("/admin/templates")
async def templates_list_page(request: Request, current_user=Depends(require_admin_page)):
    async with async_session() as session:
        items = (await session.execute(select(DocumentTemplate).order_by(DocumentTemplate.name))).scalars().all()

    return templates.TemplateResponse(request, "templates_list.html", {
        "active_page": "templates",
        "current_user": current_user,
        "nav_badges": await get_sidebar_badges(),
        "items": items,
        "placeholder_hint": PLACEHOLDER_HINT,
    })


@router.get("/admin/templates/{tpl_id}")
async def template_detail_page(tpl_id: int, request: Request, current_user=Depends(require_admin_page)):
    async with async_session() as session:
        tpl = await session.get(DocumentTemplate, tpl_id)
    if not tpl:
        return RedirectResponse(url="/admin/templates?error=Шаблон+не+найден", status_code=302)

    return templates.TemplateResponse(request, "templates_detail.html", {
        "active_page": "templates",
        "current_user": current_user,
        "nav_badges": await get_sidebar_badges(),
        "tpl": tpl,
        "placeholder_hint": PLACEHOLDER_HINT,
    })


class TemplateCreate(BaseModel):
    name: str
    content: Optional[str] = ""


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None


@router.post("/api/admin/templates")
async def api_template_create(payload: TemplateCreate, current_user=Depends(require_admin_api)):
    name = clean_text(payload.name, 100)
    if not name:
        raise HTTPException(status_code=400, detail="Название шаблона обязательно")

    async with async_session() as session:
        tpl = DocumentTemplate(name=name, content=payload.content or "")
        session.add(tpl)
        await session.commit()
        await session.refresh(tpl)

    action_logger.info("admin_template_created template_id=%s actor=%s", tpl.id, current_user.login)
    return _tpl_to_dict(tpl)


@router.patch("/api/admin/templates/{tpl_id}")
async def api_template_update(tpl_id: int, payload: TemplateUpdate, current_user=Depends(require_admin_api)):
    async with async_session() as session:
        tpl = await session.get(DocumentTemplate, tpl_id)
        if not tpl:
            raise HTTPException(status_code=404, detail="Шаблон не найден")

        if payload.name is not None:
            name = clean_text(payload.name, 100)
            if not name:
                raise HTTPException(status_code=400, detail="Название шаблона обязательно")
            tpl.name = name
        if payload.content is not None:
            tpl.content = payload.content

        await session.commit()
        await session.refresh(tpl)

    action_logger.info("admin_template_updated template_id=%s actor=%s", tpl_id, current_user.login)
    return _tpl_to_dict(tpl)


@router.delete("/api/admin/templates/{tpl_id}")
async def api_template_delete(tpl_id: int, current_user=Depends(require_admin_api)):
    async with async_session() as session:
        tpl = await session.get(DocumentTemplate, tpl_id)
        if not tpl:
            raise HTTPException(status_code=404, detail="Шаблон не найден")
        await session.delete(tpl)
        await session.commit()

    action_logger.info("admin_template_deleted template_id=%s actor=%s", tpl_id, current_user.login)
    return {"ok": True}
