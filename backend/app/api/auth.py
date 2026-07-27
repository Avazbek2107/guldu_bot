from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.technician_faculty_assignment import TechnicianFacultyAssignment
from app.models.user import User
from app.schemas.auth import LoginRequest, MeResponse, ProfileUpdateRequest, TokenResponse
from app.schemas.user import serialize_user

_assignments_loader = selectinload(User.faculty_assignments).selectinload(TechnicianFacultyAssignment.faculty)

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
COOKIE_NAME = "access_token"

AVATAR_MAX_BYTES = 2 * 1024 * 1024
AVATAR_ALLOWED_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


async def _reload_me(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(select(User).where(User.id == user_id).options(_assignments_loader))
    return result.scalar_one()


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


@router.patch("/me", response_model=MeResponse)
async def update_me(
    payload: ProfileUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wants_sensitive_change = payload.username is not None or payload.new_password is not None
    if wants_sensitive_change:
        if (
            not payload.current_password
            or current_user.password_hash is None
            or not verify_password(payload.current_password, current_user.password_hash)
        ):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Joriy parol noto'g'ri")

    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.username is not None:
        current_user.username = payload.username
    if payload.new_password is not None:
        current_user.password_hash = hash_password(payload.new_password)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Bu login allaqachon band"
        ) from exc

    user = await _reload_me(db, current_user.id)
    csrf_token = request.state.jwt_payload.get("csrf", "")
    return MeResponse(csrf_token=csrf_token, user=serialize_user(user))


@router.post("/me/avatar", response_model=MeResponse)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ext = AVATAR_ALLOWED_TYPES.get(file.content_type or "")
    if ext is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Faqat JPEG, PNG yoki WEBP rasm yuklash mumkin")

    content = await file.read()
    if len(content) > AVATAR_MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rasm hajmi 2MB dan oshmasligi kerak")

    avatars_dir = Path(settings.storage_dir) / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)

    for old_ext in AVATAR_ALLOWED_TYPES.values():
        old_path = avatars_dir / f"{current_user.id}.{old_ext}"
        if old_path.exists():
            old_path.unlink()

    filename = f"{current_user.id}.{ext}"
    (avatars_dir / filename).write_bytes(content)
    current_user.avatar_path = f"avatars/{filename}"
    await db.commit()

    user = await _reload_me(db, current_user.id)
    csrf_token = request.state.jwt_payload.get("csrf", "")
    return MeResponse(csrf_token=csrf_token, user=serialize_user(user))
