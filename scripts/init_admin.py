# scripts/init_admin.py
import asyncio
import os
from sqlalchemy.future import select
from db.database import engine, async_session, Base
from db.models import User

ADMIN_TG_ID = int(os.getenv("ADMIN_TG_ID", 0))
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "")
ADMIN_NAME = os.getenv("ADMIN_NAME", "System Admin")

async def create_first_hr():
    if not ADMIN_TG_ID or not ADMIN_PHONE:
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == ADMIN_TG_ID))
        if result.scalars().first():
            return

        admin_user = User(
            telegram_id=ADMIN_TG_ID,
            phone=ADMIN_PHONE,
            full_name=ADMIN_NAME,
            role="hr",
            is_active=True,
            approval_status="approved",
            department="HR",
            position="Руководитель"
        )
        session.add(admin_user)
        await session.commit()

if __name__ == "__main__":
    asyncio.run(create_first_hr())