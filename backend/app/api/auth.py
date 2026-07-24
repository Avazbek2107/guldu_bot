from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.technician_faculty_assignment import TechnicianFacultyAssignment
from app.models.user import User
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse
from app.schemas.user import serialize_user

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
COOKIE_NAME = "access_token"


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .where(User.username == payload.username)
        .options(selectinload(User.faculty_assignments).selectinload(TechnicianFacultyAssignment.faculty))
    )
    user = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if user is not None and user.locked_until is not None and user.locked_until > now:
        remaining_minutes = max(1, int((user.locked_until - now).total_seconds() // 60) + 1)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Hisobingiz vaqtincha bloklangan. {remaining_minutes} daqiqadan keyin qayta urinib ko'ring.",
        )

    if user is None or user.password_hash is None or not verify_password(payload.password, user.password_hash):
        if user is not None:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login yoki parol noto'g'ri")

    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hisobingiz bloklangan. Super Admin bilan bog'laning.",
        )

    user.failed_login_attempts = 0
    user.locked_until = None
    await db.commit()

    issued = create_access_token(user.id, user.role.value)
    _set_auth_cookie(response, issued.token)
    return TokenResponse(csrf_token=issued.csrf_token, user=serialize_user(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me", response_model=MeResponse)
async def me(request: Request, current_user: User = Depends(get_current_user)):
    csrf_token = request.state.jwt_payload.get("csrf", "")
    return MeResponse(csrf_token=csrf_token, user=serialize_user(current_user))
