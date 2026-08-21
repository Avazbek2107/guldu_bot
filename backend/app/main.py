import os

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jwt import PyJWTError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import auth, faculties, inventory, projects, service_payments, stats, storage, tickets, users
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token

app = FastAPI(title="Technician Support Bot API")

# Avatars and ticket-closing attachments are served through app/api/storage.py
# (requires an authenticated session) rather than an open StaticFiles mount,
# so a filename can't just be guessed/enumerated by an unauthenticated client.
os.makedirs(os.path.join(settings.storage_dir, "avatars"), exist_ok=True)
os.makedirs(os.path.join(settings.storage_dir, "ticket_attachments"), exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSRF_PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    if request.method in CSRF_PROTECTED_METHODS and request.url.path != "/auth/login":
        cookie_token = request.cookies.get(auth.COOKIE_NAME)
        if cookie_token is not None:
            try:
                payload = decode_access_token(cookie_token)
            except PyJWTError:
                payload = None
            header_csrf = request.headers.get("x-csrf-token")
            if payload is None or not header_csrf or header_csrf != payload.get("csrf"):
                return JSONResponse(status_code=403, content={"detail": "CSRF token noto'g'ri yoki yo'q"})
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


app.include_router(auth.router)
app.include_router(faculties.router)
app.include_router(users.router)
app.include_router(tickets.router)
app.include_router(stats.router)
app.include_router(inventory.router)
app.include_router(projects.router)
app.include_router(service_payments.router)
app.include_router(storage.router)


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
