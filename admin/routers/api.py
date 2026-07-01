from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from db.models import User, Request
from db.database import get_session

router = APIRouter(prefix="/api/requests")


# Read
@router.get("/")
async def get_requests(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Request))
    return result.scalars().all()


# Update
@router.put("/{request_id}")
async def update_request_status(request_id: int, status: str, telegram_id: int,
                                session: AsyncSession = Depends(get_session)):
    await session.execute(
        update(Request).where(Request.id == request_id).values(status=status)
    )
    await session.commit()

    # Инициация уведомления
    await notify_user(telegram_id, status)
    return {"status": "updated"}


# Delete
@router.delete("/{request_id}")
async def delete_request(request_id: int, session: AsyncSession = Depends(get_session)):
    await session.execute(delete(Request).where(Request.id == request_id))
    await session.commit()
    return {"status": "deleted"}