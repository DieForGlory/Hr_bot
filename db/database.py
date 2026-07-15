# db/database.py
import os
import json
from dotenv import load_dotenv
from sqlalchemy import text
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


# --- Лёгкие миграции для SQLite ------------------------------------------------
# Схема создаётся через Base.metadata.create_all (без Alembic). create_all не
# добавляет новые колонки в уже существующие таблицы, поэтому при добавлении полей
# в модели нужно один раз выполнить ALTER TABLE на прод-БД. Делаем это идемпотентно
# на старте (проверяем PRAGMA table_info). Новые ТАБЛИЦЫ создаёт сам create_all.
_EXPECTED_COLUMNS = {
    "users": {
        "work_state": "VARCHAR",
        "hire_date": "VARCHAR",
        "used_work_days": "FLOAT",
        "used_calendar_days": "FLOAT",
    },
}


async def run_migrations():
    if engine.dialect.name != "sqlite":
        # Для не-SQLite (dev/тесты) полагаемся на create_all; авто-ALTER не делаем.
        return
    async with engine.begin() as conn:
        for table, columns in _EXPECTED_COLUMNS.items():
            res = await conn.exec_driver_sql(f"PRAGMA table_info({table})")
            existing = {row[1] for row in res.fetchall()}
            if not existing:
                # таблицы ещё нет — её создаст create_all, миграция не нужна
                continue
            for col, ddl_type in columns.items():
                if col not in existing:
                    await conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {col} {ddl_type}")


async def seed_employees(db: AsyncSession):
    """Идемпотентный импорт справочника сотрудников из JSON-файла.

    ВАЖНО: файл содержит персональные данные сотрудников (ФИО, даты рождения,
    кадровое состояние), поэтому в репозитории он НЕ хранится. Его кладут рядом с
    БД — в смонтированный том ./data (в контейнере /app/data). Путь можно
    переопределить переменной окружения EMPLOYEES_SEED_PATH. Сгенерировать файл из
    кадрового Excel: python scripts/parse_employees_xls.py <Шр.xls> data/employees_seed.json
    Если файла нет — импорт просто пропускается.

    Каждая запись создаётся как directory-User: без telegram_id, is_active=False,
    approval_status="directory". При регистрации сотрудник выбирает себя из этого
    списка и «занимает» запись (привязывает telegram_id). Руководители линкуются
    по ФИО вторым проходом.
    """
    from db.models import User
    from sqlalchemy.future import select as _select

    path = os.getenv("EMPLOYEES_SEED_PATH", os.path.join("data", "employees_seed.json"))
    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as f:
        records = json.load(f)

    existing_users = (await db.execute(_select(User))).scalars().all()
    existing_names = {u.full_name for u in existing_users}

    created = 0
    for rec in records:
        if rec["full_name"] in existing_names:
            continue
        db.add(User(
            full_name=rec["full_name"],
            position=rec.get("position") or None,
            department=rec.get("department"),
            role=rec.get("role", "employee"),
            birth_date=rec.get("birth_date"),
            work_state=rec.get("work_state"),
            approval_status="directory",
            is_active=False,
            telegram_id=None,
            vacation_days_balance=0,
            language="ru",
        ))
        created += 1
    if created:
        await db.commit()

    # Второй проход: привязка руководителей по ФИО (только если ещё не задан).
    users = (await db.execute(_select(User))).scalars().all()
    by_name = {u.full_name: u for u in users}
    linked = 0
    for rec in records:
        emp = by_name.get(rec["full_name"])
        mgr_name = rec.get("manager_name")
        if not emp or not mgr_name or emp.manager_id is not None:
            continue
        mgr = by_name.get(mgr_name)
        if mgr and mgr.id != emp.id:
            emp.manager_id = mgr.id
            linked += 1
    if linked:
        await db.commit()

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