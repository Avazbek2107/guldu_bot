from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(
    role: UserRole | None = None,
    faculty_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(User)

    if current_user.role == UserRole.SUPER_ADMIN:
        if role is not None:
            query = query.where(User.role == role)
        if faculty_id is not None:
            query = query.where(User.faculty_id == faculty_id)
    elif current_user.role in (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP):
        # Technicians may only see fellow technicians in their own faculty
        # (needed for the reassign dropdown), not the full user directory.
        query = query.where(
            User.faculty_id == current_user.faculty_id,
            User.role.in_([UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP]),
        )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")

    result = await db.execute(query.order_by(User.id))
    return result.scalars().all()


@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        role=payload.role,
        faculty_id=payload.faculty_id,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu username band yoki fakultetda allaqachon asosiy texnik xodim bor",
        ) from exc
    await db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut, dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))])
async def update_user(user_id: int, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi")

    data = payload.model_dump(exclude_unset=True, exclude={"password"})
    for field, value in data.items():
        setattr(user, field, value)
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)

    await db.commit()
    await db.refresh(user)
    return user


@router.post(
    "/{user_id}/block", response_model=UserOut, dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))]
)
async def block_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi")
    user.is_blocked = True
    await db.commit()
    await db.refresh(user)
    return user


@router.post(
    "/{user_id}/unblock", response_model=UserOut, dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))]
)
async def unblock_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi")
    user.is_blocked = False
    await db.commit()
    await db.refresh(user)
    return user


@router.delete(
    "/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))]
)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi")
    await db.delete(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu foydalanuvchi bildirishnomalarga bog'langan, o'chirib bo'lmaydi. Buning o'rniga bloklang.",
        ) from exc
