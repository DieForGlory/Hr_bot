import asyncio
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.database import async_session, engine, Base
from db.models import User

EXCEL_FILE = "Структура.xlsx"


async def import_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    df = pd.read_excel(EXCEL_FILE)
    df = df.fillna("")

    async with async_session() as session:
        # Этап 1: Загрузка всех сотрудников (без привязки к руководителям)
        for _, row in df.iterrows():
            phone = str(row.get("Телефон", "")).strip().replace("+", "")
            if not phone:
                continue

            existing = await session.execute(select(User).where(User.phone == phone))
            if existing.scalars().first():
                continue

            user = User(
                full_name=row.get("ФИО", "").strip(),
                phone=phone,
                role=row.get("Роль", "employee").strip().lower(),
                vacation_days_balance=int(row.get("Баланс отпуска", 0))
            )
            session.add(user)
        await session.commit()

        # Этап 2: Выстраивание иерархии (manager_id)
        for _, row in df.iterrows():
            manager_name = row.get("ФИО Руководителя", "").strip()
            if not manager_name:
                continue

            emp_phone = str(row.get("Телефон", "")).strip().replace("+", "")

            emp_query = await session.execute(select(User).where(User.phone == emp_phone))
            employee = emp_query.scalars().first()

            mgr_query = await session.execute(select(User).where(User.full_name == manager_name))
            manager = mgr_query.scalars().first()

            if employee and manager:
                employee.manager_id = manager.id

        await session.commit()
        print("Импорт иерархии из Структура.xlsx успешно завершен.")


if __name__ == "__main__":
    asyncio.run(import_data())