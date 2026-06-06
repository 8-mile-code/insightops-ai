from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(prefix="/db", tags=["Database"])


@router.get("/ping")
async def ping_database(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str | int]:
    result = await session.execute(text("SELECT 1"))
    value = result.scalar_one()

    return {
        "status": "ok",
        "result": value,
    }
