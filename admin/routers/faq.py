# admin/routers/faq.py
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from admin.templating import templates
from admin.gateway_auth import require_permission
from admin.context import get_sidebar_badges
from db.database import async_session
from db.models import FAQ
from bot.utils.validators import clean_text
from core.logging_config import action_logger

router = APIRouter()


def _faq_to_dict(f: FAQ) -> dict:
    return {"id": f.id, "question": f.question, "answer": f.answer}


@router.get("/admin/faq")
async def faq_list_page(request: Request, current_user=Depends(require_permission("hr_bot.faq.view"))):
    async with async_session() as session:
        items = (await session.execute(select(FAQ).order_by(FAQ.id))).scalars().all()

    return templates.TemplateResponse(request, "faq_list.html", {
        "active_page": "faq",
        "current_user": current_user,
        "nav_badges": await get_sidebar_badges(),
        "items": items,
    })


class FaqCreate(BaseModel):
    question: str
    answer: str


class FaqUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None


@router.post("/api/admin/faq")
async def api_faq_create(payload: FaqCreate, current_user=Depends(require_permission("hr_bot.faq.manage"))):
    question = clean_text(payload.question, 500)
    answer = clean_text(payload.answer, 4000)
    if not question or not answer:
        raise HTTPException(status_code=400, detail="Вопрос и ответ обязательны")

    async with async_session() as session:
        faq = FAQ(question=question, answer=answer)
        session.add(faq)
        await session.commit()
        await session.refresh(faq)

    action_logger.info("admin_faq_created faq_id=%s actor=%s", faq.id, current_user.username)
    return _faq_to_dict(faq)


@router.patch("/api/admin/faq/{faq_id}")
async def api_faq_update(faq_id: int, payload: FaqUpdate, current_user=Depends(require_permission("hr_bot.faq.manage"))):
    async with async_session() as session:
        faq = await session.get(FAQ, faq_id)
        if not faq:
            raise HTTPException(status_code=404, detail="Вопрос не найден")

        if payload.question is not None:
            question = clean_text(payload.question, 500)
            if not question:
                raise HTTPException(status_code=400, detail="Вопрос не может быть пустым")
            faq.question = question
        if payload.answer is not None:
            answer = clean_text(payload.answer, 4000)
            if not answer:
                raise HTTPException(status_code=400, detail="Ответ не может быть пустым")
            faq.answer = answer

        await session.commit()
        await session.refresh(faq)

    action_logger.info("admin_faq_updated faq_id=%s actor=%s", faq_id, current_user.username)
    return _faq_to_dict(faq)


@router.delete("/api/admin/faq/{faq_id}")
async def api_faq_delete(faq_id: int, current_user=Depends(require_permission("hr_bot.faq.manage"))):
    async with async_session() as session:
        faq = await session.get(FAQ, faq_id)
        if not faq:
            raise HTTPException(status_code=404, detail="Вопрос не найден")
        await session.delete(faq)
        await session.commit()

    action_logger.info("admin_faq_deleted faq_id=%s actor=%s", faq_id, current_user.username)
    return {"ok": True}
