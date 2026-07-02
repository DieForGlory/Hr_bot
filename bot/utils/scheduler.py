from datetime import date, datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select
from db.database import async_session
from db.models import Request, User
from aiogram import Bot
from bot.locales.texts import get_text
from core.logging_config import action_logger

_scheduler: AsyncIOScheduler | None = None


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
                    get_text("vacation_first_day", user.language)
                )
            except Exception:
                pass


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(check_vacations_starting_today, 'cron', hour=9, minute=0, args=[bot])
    action_logger.info("scheduler_started")
    return _scheduler


async def _send_sick_leave_reminder(bot: Bot, telegram_id: int):
    lang = "ru"
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalars().first()
        if user:
            lang = user.language

    try:
        await bot.send_message(telegram_id, get_text("sick_reminder_3days", lang))
    except Exception:
        pass


def schedule_sick_leave_reminder(bot: Bot, telegram_id: int) -> None:
    """Регистрирует напоминание через 3 дня после подачи заявки на больничный."""
    if _scheduler is None:
        return

    run_date = datetime.now() + timedelta(days=3)
    _scheduler.add_job(
        _send_sick_leave_reminder,
        trigger='date',
        run_date=run_date,
        args=[bot, telegram_id]
    )
