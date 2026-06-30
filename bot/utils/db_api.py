
from sqlalchemy.future import select
from sqlalchemy import update
from db.database import async_session
from db.models import User, Request

async def get_user_by_telegram_id(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalars().first()

async def create_request(user_id: int, req_type: str, start_date=None, end_date=None, comment=None):
    async with async_session() as session:
        new_req = Request(
            user_id=user_id,
            type=req_type,
            start_date=start_date,
            end_date=end_date,
            comment=comment
        )
        session.add(new_req)
        await session.commit()
        return new_req.id

async def get_user_requests(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Request).where(Request.user_id == user_id))
        return result.scalars().all()