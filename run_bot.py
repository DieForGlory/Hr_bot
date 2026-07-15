import asyncio
from db.database import engine, Base, async_session, seed_faq, seed_templates, seed_employees, run_migrations
import db.models
from core.logging_config import setup_logging

from aiogram import Bot, Dispatcher
from core.config import BOT_TOKEN
from bot.handlers import auth, main_menu, vacation, certificates, sick_leave, approvals, hr_question, settings
from bot.utils.scheduler import setup_scheduler

async def main():
    setup_logging()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Лёгкие ALTER TABLE для новых колонок в существующих таблицах (SQLite).
    await run_migrations()

    async with async_session() as session:
        await seed_faq(session)
        await seed_templates(session)
        await seed_employees(session)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(auth.router)
    dp.include_router(main_menu.router)
    dp.include_router(vacation.router)
    dp.include_router(certificates.router)
    dp.include_router(sick_leave.router)
    dp.include_router(approvals.router)
    dp.include_router(hr_question.router)
    dp.include_router(settings.router)

    scheduler = setup_scheduler(bot)
    scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())