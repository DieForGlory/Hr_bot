# admin/routers/api.py
import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, insert
from datetime import date
from db.database import get_db
from db.models import User, DocumentTemplate, CalendarDay

router = APIRouter(prefix="/api")


@router.post("/users/{user_id}/role")
async def update_user_role(user_id: int, role: str = Form(...), db: AsyncSession = Depends(get_db)):
    await db.execute(update(User).where(User.id == user_id).values(role=role))
    await db.commit()
    return {"status": "success"}


@router.post("/templates/upload")
async def upload_template(name: str = Form(...), file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    os.makedirs("assets/templates", exist_ok=True)
    file_path = f"assets/templates/{file.filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    await db.execute(insert(DocumentTemplate).values(name=name, file_path=file_path))
    await db.commit()
    return {"status": "success"}


@router.post("/calendar/add")
async def add_calendar_day(day_date: date = Form(...), is_workday: bool = Form(...), description: str = Form(""),
                           db: AsyncSession = Depends(get_db)):
    await db.execute(insert(CalendarDay).values(date=day_date, is_workday=is_workday, description=description))
    await db.commit()
    return {"status": "success"}