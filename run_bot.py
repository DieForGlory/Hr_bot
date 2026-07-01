import asyncio
import aiohttp
from db.database import engine, Base
import db.models
_orig_connector_init = aiohttp.TCPConnector.__init__

def _patched_connector_init(self, *args, **kwargs):
    kwargs['ssl'] = False
    _orig_connector_init(self, *args, **kwargs)

aiohttp.TCPConnector.__init__ = _patched_connector_init

from aiogram import Bot, Dispatcher
from core.config import BOT_TOKEN
from bot.handlers import auth, main_menu, vacation, certificates, sick_leave, approvals, hr_question, settings

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())