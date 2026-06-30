
from sqlalchemy.future import select
from sqlalchemy import update
from db.database import async_session
from db.models import User, Request
from sqlalchemy import update
from db.database import async_session
from db.models import User
from sqlalchemy.future import select
from sqlalchemy import update

async def get_request_by_id(req_id: int):
    async with async_session() as session:
        result = await session.execute(select(Request).where(Request.id == req_id))
        return result.scalars().first()

async def update_request_status(req_id: int, status: str, hr_comment: str = None):
    async with async_session() as session:
        values = {"status": status}
        if hr_comment:
            values["hr_comment"] = hr_comment
        await session.execute(update(Request).where(Request.id == req_id).values(**values))
        await session.commit()

async def get_user_by_id(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

async def get_users_by_role(role: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.role == role))
        return result.scalars().all()

async def get_user_by_phone(phone: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.phone.like(f"%{phone[-10:]}%")))
        return result.scalars().first()

async def update_user_telegram_id(user_id: int, telegram_id: int):
    async with async_session() as session:
        await session.execute(update(User).where(User.id == user_id).values(telegram_id=telegram_id))
        await session.commit()

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