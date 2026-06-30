import asyncio
from aiogram import Bot

async def schedule_sick_leave_reminder(bot: Bot, chat_id: int, delay_days: int = 3):
    await asyncio.sleep(delay_days * 86400)
    await bot.send_message(
        chat_id=chat_id,
        text="Напоминаем о необходимости прикрепить подтверждающий документ после завершения больничного."
    )