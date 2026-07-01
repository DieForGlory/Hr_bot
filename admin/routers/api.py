import ssl
import aiohttp
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from db.models import Request as HRRequest
from db.database import engine
from core.config import BOT_TOKEN

router = APIRouter(prefix="/api/requests", tags=["Requests"])

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
connector = aiohttp.TCPConnector(ssl=ssl_context)
session = AiohttpSession()


async def create_client_session():
    return aiohttp.ClientSession(connector=connector)


session._create_client_session = create_client_session

bot = Bot(token=BOT_TOKEN, session=session)


class StatusUpdate(BaseModel):
    status: str


async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session


@router.get("/")
async def get_requests(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(HRRequest))
    return result.scalars().all()


@router.put("/{request_id}")
async def update_request(request_id: int, payload: StatusUpdate, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(HRRequest).where(HRRequest.id == request_id))
    db_req = result.scalar_one_or_none()

    if not db_req:
        raise HTTPException(status_code=404, detail="Request not found")

    db_req.status = payload.status
    await db.commit()

    try:
        await bot.send_message(
            chat_id=db_req.telegram_id,
            text=f"Статус вашей заявки обновлен: {payload.status}"
        )
    except Exception as e:
        print(f"Notification error: {e}")

    return {"status": "success", "new_status": payload.status}