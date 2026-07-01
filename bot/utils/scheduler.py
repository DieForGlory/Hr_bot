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

async def _send_sick_leave_reminder(bot, user_id: int):
    try:
        await bot.send_message(user_id, "Напоминание: предоставьте закрытый лист нетрудоспособности в HR-отдел.")
    except Exception:
        pass

def schedule_sick_leave_reminder(*args, **kwargs):
    """
    Универсальная обертка планировщика.
    Ожидаемые позиционные или именованные аргументы: scheduler, bot, user_id, run_date
    """
    scheduler = kwargs.get('scheduler') or (args[0] if len(args) > 0 else None)
    bot = kwargs.get('bot') or (args[1] if len(args) > 1 else None)
    user_id = kwargs.get('user_id') or (args[2] if len(args) > 2 else None)
    run_date = kwargs.get('run_date') or (args[3] if len(args) > 3 else None)

    if scheduler and bot and user_id and run_date:
        scheduler.add_job(
            _send_sick_leave_reminder,
            trigger='date',
            run_date=run_date,
            args=[bot, user_id]
        )