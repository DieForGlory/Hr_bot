# admin/main.py
from fastapi import FastAPI, Request as FastAPIRequest, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.database import engine, Base, get_db
from db.models import User, Request as HRRequest, DocumentTemplate, CalendarDay
import logging

app = FastAPI(title="HR Bot Admin Panel")
templates = Jinja2Templates(directory="admin/templates")


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/api/turbo") == -1

logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def dashboard(request: FastAPIRequest, db: AsyncSession = Depends(get_db)):
    users = (await db.execute(select(User))).scalars().all()
    requests_data = (await db.execute(select(HRRequest))).scalars().all()
    templates_data = (await db.execute(select(DocumentTemplate))).scalars().all()
    calendar_data = (await db.execute(select(CalendarDay).order_by(CalendarDay.date))).scalars().all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "users": users,
        "requests": requests_data,
        "templates": templates_data,
        "calendar": calendar_data
    })