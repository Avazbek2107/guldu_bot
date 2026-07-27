from fastapi import Cookie, Depends, HTTPException, Request, status
from jwt import PyJWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.enums import UserRole
from app.models.technician_faculty_assignment import TechnicianFacultyAssignment
from app.models.user import User

_assignments_loader = selectinload(User.faculty_assignments).selectinload(TechnicianFacultyAssignment.faculty)


def technician_faculty_ids(user: User) -> set[int]:
    return {a.faculty_id for a in user.faculty_assignments}


async def get_current_user(
    request: Request,
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Yaroqsiz yoki muddati o'tgan token",
    )
    if access_token is None:
        raise credentials_exception
    try:
        payload = decode_access_token(access_token)
        user_id = int(payload["sub"])
    except (PyJWTError, KeyError, ValueError):
        raise credentials_exception
    request.state.jwt_payload = payload

    result = await db.execute(select(User).where(User.id == user_id).options(_assignments_loader))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hisobingiz bloklangan. Super Admin bilan bog'laning.",
        )
    return user


def require_roles(*roles: UserRole):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu amal uchun ruxsatingiz yo'q",
            )
        return current_user

    return checker


def has_permission(user: User, resource: str, action: str = "view") -> bool:
    if user.role == UserRole.SUPER_ADMIN:
        return True
    if user.role == UserRole.ADMIN:
        return action in (user.permissions or {}).get(resource, [])
    return False


def require_permission(resource: str, action: str = "view"):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu amal uchun ruxsatingiz yo'q",
            )
        return current_user

    return checker
