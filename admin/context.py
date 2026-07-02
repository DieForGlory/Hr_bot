# admin/context.py
from sqlalchemy import func, select, or_
from db.database import async_session
from db.models import User, Request


async def get_sidebar_badges() -> dict:
    async with async_session() as session:
        pending_users = (await session.execute(
            select(func.count(User.id)).where(User.approval_status == "pending")
        )).scalar_one()

        pending_requests = (await session.execute(
            select(func.count(Request.id)).where(
                or_(
                    Request.status == "pending",
                    Request.status == "manager_approved",
                    Request.status == "in_progress",
                )
            )
        )).scalar_one()

    return {"pending_users": pending_users, "pending_requests": pending_requests}
