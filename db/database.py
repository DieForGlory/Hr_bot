# db/database.py
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

try:
    load_dotenv()
except Exception:
    # В контейнере переменные приходят из compose (env_file/environment),
    # поэтому битая кодировка .env не должна ронять запуск.
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///hr_bot.db")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session

# Часть ответов ниже помечена как "уточняется" — нет исходных данных по расчётам
# (декретные/больничные/аванс и т.д.), реальный текст должен предоставить HR перед запуском в прод.
_NEEDS_HR_INPUT = "Уточняется, обратитесь в HR-отдел."

async def seed_faq(db: AsyncSession):
    from db.models import FAQ
    from sqlalchemy.future import select as _select

    existing = (await db.execute(_select(FAQ))).scalars().first()
    if existing:
        return

    questions = [
        ("В какие даты выплачивается аванс и заработная плата?",
         "Аванс выплачивается 15-го числа, заработная плата — 30-го."),
        ("Сколько дней отпуска положено работнику?",
         "Ежегодный оплачиваемый отпуск составляет 21 календарный день."),
        ("Как рассчитываются отпускные?", _NEEDS_HR_INPUT),
        ("Как рассчитывается аванс и заработная плата?", _NEEDS_HR_INPUT),
        ("Как рассчитываются больничные?", _NEEDS_HR_INPUT),
        ("Как рассчитываются декретные?", _NEEDS_HR_INPUT),
        ("Где скачать персональные документы?",
         "Через раздел «Справки» в главном меню бота."),
        ("Где проверить стаж работы?", _NEEDS_HR_INPUT),
        ("Кто может восстановить стаж работы?", _NEEDS_HR_INPUT),
        ("Где скачать больничный лист?", _NEEDS_HR_INPUT),
    ]
    for q, a in questions:
        db.add(FAQ(question=q, answer=a))
    await db.commit()


async def seed_templates(db: AsyncSession):
    """Создаёт дефолтный шаблон приказа об отпуске, чтобы его можно было редактировать в админке."""
    from db.models import DocumentTemplate
    from sqlalchemy.future import select as _select
    from bot.utils.constants import DEFAULT_VACATION_ORDER_TEMPLATE

    existing = (await db.execute(
        _select(DocumentTemplate).where(DocumentTemplate.name == "Отпуск")
    )).scalars().first()
    if existing:
        return

    db.add(DocumentTemplate(name="Отпуск", content=DEFAULT_VACATION_ORDER_TEMPLATE))
    await db.commit()