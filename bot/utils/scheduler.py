from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import date
from sqlalchemy.future import select
from db.database import async_session
from db.models import Request, User
from aiogram import Bot

async def check_vacations_starting_today(bot: Bot):
    today = date.today()
    async with async_session() as session:
        result = await session.execute(
            select(Request, User).join(User, Request.user_id == User.id).where(
                Request.type.in_(["vacation_paid", "vacation_unpaid"]),
                Request.start_date == today,
                Request.status == "hr_approved"
            )
        )
        records = result.all()

    for req, user in records:
        if user.telegram_id:
            try:
                await bot.send_message(
                    user.telegram_id,
                    "Желаем вам отличного отпуска! 😊"
                )
            except Exception:
                pass

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_vacations_starting_today, 'cron', hour=9, minute=0, args=[bot])
    return scheduler