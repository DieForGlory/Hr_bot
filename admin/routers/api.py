# admin/routers/api.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from db.database import get_db
from db.models import Request

router = APIRouter(prefix="/api")

@router.post("/requests/{req_id}/status")
async def change_request_status(req_id: int, status: str, db: AsyncSession = Depends(get_db)):
    await db.execute(
        update(Request).where(Request.id == req_id).values(status=status)
    )
    await db.commit()
    return {"status": "ok"}