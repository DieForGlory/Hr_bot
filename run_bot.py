
import asyncio
import logging
from aiogram import Bot, Dispatcher
from core.config import BOT_TOKEN
from db.database import engine, Base
from bot.handlers import auth, main_menu, vacation, certificates, sick_leave, approvals

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(main_menu.router)
    dp.include_router(vacation.router)
    dp.include_router(certificates.router)
    dp.include_router(sick_leave.router)
    dp.include_router(auth.router)
    dp.include_router(approvals.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())