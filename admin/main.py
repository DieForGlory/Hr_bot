from fastapi import FastAPI, Request as FastAPIRequest, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.database import engine, Base, get_db
from db.models import User, Request as HRRequest

app = FastAPI(title="HR Bot Admin Panel")
templates = Jinja2Templates(directory="admin/templates")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def dashboard(request: FastAPIRequest, db: AsyncSession = Depends(get_db)):
    result_users = await db.execute(select(User))
    users = result_users.scalars().all()

    result_reqs = await db.execute(select(HRRequest))
    requests = result_reqs.scalars().all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "users": users,
        "requests": requests
    })