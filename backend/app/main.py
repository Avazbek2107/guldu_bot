from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import auth, faculties, users
from app.core.database import get_db

app = FastAPI(title="Technician Support Bot API")

app.include_router(auth.router)
app.include_router(faculties.router)
app.include_router(users.router)


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
