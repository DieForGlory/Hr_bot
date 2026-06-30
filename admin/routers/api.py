# admin/routers/api.py
from fastapi import APIRouter, Depends
from db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Request
from sqlalchemy import update

router = APIRouter()

@router.post("/requests/{req_id}/status")
async def update_status(req_id: int, status: str, db: AsyncSession = Depends(get_db)):
    await db.execute(update(Request).where(Request.id == req_id).values(status=status))
    await db.commit()
    return {"status": "success"}