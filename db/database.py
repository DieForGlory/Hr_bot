# db/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

DATABASE_URL = "sqlite+aiosqlite:///hr_bot.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session

async def seed_faq(db: AsyncSession):
    questions = [
        ("Когда зарплата?", "Аванс выплачивается 15-го числа, заработная плата — 30-го."),
        ("Сколько дней отпуска?", "Ежегодный оплачиваемый отпуск составляет 21 календарный день.")
    ]
    for q, a in questions:
        db.add(FAQ(question=q, answer=a))
    await db.commit()