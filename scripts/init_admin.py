# scripts/init_admin.py
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.future import select
from db.database import engine, async_session, Base
from db.models import User
from admin.security import hash_password

ADMIN_TG_ID = int(os.getenv("ADMIN_TG_ID", 0))
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "")
ADMIN_NAME = os.getenv("ADMIN_NAME", "System Admin")
ADMIN_LOGIN = os.getenv("ADMIN_LOGIN", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


async def _ensure_user_columns(conn):
    """В проекте нет Alembic: на уже существующей таблице users новые колонки
    (login/password_hash) сами не появятся из create_all — добавляем идемпотентно."""
    result = await conn.execute(text("PRAGMA table_info(users)"))
    existing_columns = {row[1] for row in result.fetchall()}
    if not existing_columns:
        return  # таблицы ещё нет, create_all создаст её сразу с нужными колонками
    if "login" not in existing_columns:
        await conn.execute(text("ALTER TABLE users ADD COLUMN login VARCHAR"))
    if "password_hash" not in existing_columns:
        await conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))


async def create_first_hr():
    async with engine.begin() as conn:
        await _ensure_user_columns(conn)
        await conn.run_sync(Base.metadata.create_all)

    if not ADMIN_TG_ID or not ADMIN_PHONE:
        return

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == ADMIN_TG_ID))
        admin_user = result.scalars().first()

        if not admin_user:
            admin_user = User(
                telegram_id=ADMIN_TG_ID,
                phone=ADMIN_PHONE,
                full_name=ADMIN_NAME,
                role="hr",
                is_active=True,
                approval_status="approved",
                department="HR",
                position="Руководитель"
            )
            session.add(admin_user)
            await session.commit()

        # Логин/пароль выставляем только один раз, чтобы не затирать пароль,
        # который HR мог сменить через веб-админку
        if ADMIN_LOGIN and ADMIN_PASSWORD and not admin_user.login:
            admin_user.login = ADMIN_LOGIN
            admin_user.password_hash = hash_password(ADMIN_PASSWORD)
            await session.commit()

if __name__ == "__main__":
    asyncio.run(create_first_hr())
