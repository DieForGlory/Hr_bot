# admin/routers/calendar.py
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, extract

from admin.templating import templates
from admin.gateway_auth import require_permission
from admin.context import get_sidebar_badges
from db.database import async_session
from db.models import CalendarDay
from core.logging_config import action_logger

router = APIRouter()

MAX_BULK_DAYS = 366


def _day_to_dict(d: CalendarDay) -> dict:
    return {"id": d.id, "date": d.date.isoformat(), "is_workday": d.is_workday, "description": d.description}


@router.get("/admin/calendar")
async def calendar_list_page(request: Request, current_user=Depends(require_permission("hr_bot.calendar.view"))):
    today = date.today()
    return templates.TemplateResponse(request, "calendar_list.html", {
        "active_page": "calendar",
        "current_user": current_user,
        "nav_badges": await get_sidebar_badges(),
        "current_year": today.year,
    })


@router.get("/api/admin/calendar")
async def api_calendar_list(year: Optional[int] = None, month: Optional[int] = None, current_user=Depends(require_permission("hr_bot.calendar.view"))):
    async with async_session() as session:
        stmt = select(CalendarDay)
        if year:
            stmt = stmt.where(extract("year", CalendarDay.date) == year)
        if month:
            stmt = stmt.where(extract("month", CalendarDay.date) == month)
        stmt = stmt.order_by(CalendarDay.date)
        items = (await session.execute(stmt)).scalars().all()

    return {"items": [_day_to_dict(d) for d in items]}


class DayCreate(BaseModel):
    date: date
    is_workday: bool = False
    description: Optional[str] = None


class DayUpdate(BaseModel):
    is_workday: Optional[bool] = None
    description: Optional[str] = None


class BulkCreate(BaseModel):
    date_from: date
    date_to: date
    is_workday: bool = False
    description: Optional[str] = None


@router.post("/api/admin/calendar")
async def api_calendar_create(payload: DayCreate, current_user=Depends(require_permission("hr_bot.calendar.manage"))):
    async with async_session() as session:
        existing = (await session.execute(select(CalendarDay).where(CalendarDay.date == payload.date))).scalars().first()
        if existing:
            raise HTTPException(status_code=409, detail="Такая дата уже есть в календаре")

        day = CalendarDay(date=payload.date, is_workday=payload.is_workday, description=payload.description)
        session.add(day)
        await session.commit()
        await session.refresh(day)

    action_logger.info("admin_calendar_day_created date=%s actor=%s", payload.date, current_user.username)
    return _day_to_dict(day)


@router.post("/api/admin/calendar/bulk")
async def api_calendar_bulk_create(payload: BulkCreate, current_user=Depends(require_permission("hr_bot.calendar.manage"))):
    if payload.date_to < payload.date_from:
        raise HTTPException(status_code=400, detail="Дата «по» не может быть раньше даты «с»")

    total_days = (payload.date_to - payload.date_from).days + 1
    if total_days > MAX_BULK_DAYS:
        raise HTTPException(status_code=400, detail=f"Слишком большой диапазон (максимум {MAX_BULK_DAYS} дней)")

    async with async_session() as session:
        existing_rows = (await session.execute(
            select(CalendarDay.date).where(
                CalendarDay.date >= payload.date_from, CalendarDay.date <= payload.date_to
            )
        )).scalars().all()
        existing_dates = set(existing_rows)

        created = 0
        d = payload.date_from
        while d <= payload.date_to:
            if d not in existing_dates:
                session.add(CalendarDay(date=d, is_workday=payload.is_workday, description=payload.description))
                created += 1
            d += timedelta(days=1)

        await session.commit()

    action_logger.info(
        "admin_calendar_bulk_created date_from=%s date_to=%s created=%s actor=%s",
        payload.date_from, payload.date_to, created, current_user.username
    )
    return {"created": created, "skipped": total_days - created}


@router.patch("/api/admin/calendar/{day_id}")
async def api_calendar_update(day_id: int, payload: DayUpdate, current_user=Depends(require_permission("hr_bot.calendar.manage"))):
    async with async_session() as session:
        day = await session.get(CalendarDay, day_id)
        if not day:
            raise HTTPException(status_code=404, detail="Запись не найдена")

        if payload.is_workday is not None:
            day.is_workday = payload.is_workday
        if payload.description is not None:
            day.description = payload.description

        await session.commit()
        await session.refresh(day)

    action_logger.info("admin_calendar_day_updated day_id=%s actor=%s", day_id, current_user.username)
    return _day_to_dict(day)


@router.delete("/api/admin/calendar/{day_id}")
async def api_calendar_delete(day_id: int, current_user=Depends(require_permission("hr_bot.calendar.manage"))):
    async with async_session() as session:
        day = await session.get(CalendarDay, day_id)
        if not day:
            raise HTTPException(status_code=404, detail="Запись не найдена")
        await session.delete(day)
        await session.commit()

    action_logger.info("admin_calendar_day_deleted day_id=%s actor=%s", day_id, current_user.username)
    return {"ok": True}
