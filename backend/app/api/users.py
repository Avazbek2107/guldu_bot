from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, has_permission, technician_faculty_ids
from app.core.database import get_db
from app.core.security import hash_password
from app.models.enums import TechnicianFacultyRole, UserRole
from app.models.technician_faculty_assignment import TechnicianFacultyAssignment
from app.models.user import User
from app.schemas.user import (
    FacultyAssignmentIn,
    UserCreate,
    UserOut,
    UserUpdate,
    serialize_user,
    validate_faculty_assignments,
    validate_permissions,
)

router = APIRouter(prefix="/users", tags=["users"])

TECHNICIAN_ROLES = (UserRole.TECHNICIAN_MAIN, UserRole.TECHNICIAN_BACKUP)

_assignments_loader = selectinload(User.faculty_assignments).selectinload(TechnicianFacultyAssignment.faculty)


async def _apply_assignments(db: AsyncSession, user: User, assignments: list[FacultyAssignmentIn]) -> None:
    await db.execute(delete(TechnicianFacultyAssignment).where(TechnicianFacultyAssignment.user_id == user.id))
    await db.flush()

    for assignment in assignments:
        if assignment.role == TechnicianFacultyRole.TECHNICIAN_MAIN:
            await db.execute(
                update(TechnicianFacultyAssignment)
                .where(
                    TechnicianFacultyAssignment.faculty_id == assignment.faculty_id,
                    TechnicianFacultyAssignment.role == TechnicianFacultyRole.TECHNICIAN_MAIN,
                    TechnicianFacultyAssignment.user_id != user.id,
                )
                .values(role=TechnicianFacultyRole.TECHNICIAN_BACKUP)
            )
        db.add(TechnicianFacultyAssignment(user_id=user.id, faculty_id=assignment.faculty_id, role=assignment.role))
    await db.flush()


async def _load_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id).options(_assignments_loader))
    return result.scalar_one_or_none()


def _resource_for_role(role: UserRole) -> str:
    return "end_users" if role == UserRole.FACULTY_STAFF else "users"


def _can_manage_target_role(current_user: User, target_role: UserRole) -> bool:
    # Even an Admin granted full "users" CRUD permission must never create, edit,
    # block or delete a Super Admin or fellow Admin account — that would let a
    # delegated Admin escalate their own (or an ally's) privileges. Only a real
    # Super Admin may manage accounts at this tier.
    if target_role in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
        return current_user.role == UserRole.SUPER_ADMIN
    return True


@router.get("", response_model=list[UserOut])
async def list_users(
    role: str | None = None,
    faculty_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(User).options(_assignments_loader)
    own_faculty_ids: set[int] | None = None

    parsed_roles: list[UserRole] | None = None
    if role:
        try:
            parsed_roles = [UserRole(r) for r in role.split(",")]
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Noto'g'ri rol qiymati") from exc

    def _apply_role_and_faculty_filters() -> None:
        nonlocal query
        if parsed_roles is not None:
            query = query.where(User.role.in_(parsed_roles))
        if faculty_id is not None:
            query = query.where(User.faculty_id == faculty_id)

    resource = "end_users" if parsed_roles and all(r == UserRole.FACULTY_STAFF for r in parsed_roles) else "users"

    if current_user.role == UserRole.SUPER_ADMIN or (
        current_user.role == UserRole.ADMIN and has_permission(current_user, resource, "view")
    ):
        _apply_role_and_faculty_filters()
        if current_user.role == UserRole.ADMIN:
            # Admins must never see Super Admin accounts, regardless of the
            # role filter they request.
            query = query.where(User.role != UserRole.SUPER_ADMIN)
    elif current_user.role in TECHNICIAN_ROLES:
        # Technicians may only see fellow technicians who share at least one
        # faculty with them (needed for the reassign dropdown), not the full directory.
        own_faculty_ids = technician_faculty_ids(current_user)
        if not own_faculty_ids:
            return []
        shared_technicians = select(TechnicianFacultyAssignment.user_id).where(
            TechnicianFacultyAssignment.faculty_id.in_(own_faculty_ids)
        )
        query = query.where(User.id.in_(shared_technicians), User.role.in_(TECHNICIAN_ROLES))
    elif current_user.role == UserRole.ADMIN and parsed_roles and all(r in TECHNICIAN_ROLES for r in parsed_roles):
        # Admins without explicit "users" access can still fetch the technician
        # roster as supporting data for pages they *are* permitted to use
        # (e.g. reassigning a ticket, picking a technician for inventory).
        _apply_role_and_faculty_filters()
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")

    result = await db.execute(query.order_by(User.id))
    return [serialize_user(u, visible_faculty_ids=own_faculty_ids) for u in result.scalars().unique().all()]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if not has_permission(current_user, _resource_for_role(payload.role), "create") or not _can_manage_target_role(
        current_user, payload.role
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        role=payload.role,
        faculty_id=None,
        permissions=payload.permissions if payload.role == UserRole.ADMIN else None,
        telegram_id=payload.telegram_id,
    )
    db.add(user)
    try:
        await db.flush()
        if payload.role in TECHNICIAN_ROLES:
            await _apply_assignments(db, user, payload.faculty_assignments)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu username, Telegram ID band yoki fakultetda allaqachon asosiy texnik xodim bor",
        ) from exc

    created = await _load_user(db, user.id)
    return serialize_user(created)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await _load_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi")
    if not has_permission(current_user, _resource_for_role(user.role), "edit") or not _can_manage_target_role(
        current_user, user.role
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")

    if payload.faculty_id is not None and user.role in TECHNICIAN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Texnik xodim uchun faculty_id emas, faculty_assignments ishlatiladi",
        )

    data = payload.model_dump(exclude_unset=True, exclude={"password", "faculty_assignments", "permissions"})
    for field, value in data.items():
        setattr(user, field, value)
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)

    try:
        if payload.faculty_assignments is not None:
            validate_faculty_assignments(user.role, payload.faculty_assignments)
            await _apply_assignments(db, user, payload.faculty_assignments)
        if payload.permissions is not None:
            user.permissions = validate_permissions(user.role, payload.permissions)
        await db.commit()
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu Telegram ID allaqachon boshqa foydalanuvchiga bog'langan",
        ) from exc

    db.expire_all()
    updated = await _load_user(db, user_id)
    return serialize_user(updated)


@router.post("/{user_id}/block", response_model=UserOut)
async def block_user(
    user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    user = await _load_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi")
    if not has_permission(current_user, _resource_for_role(user.role), "edit") or not _can_manage_target_role(
        current_user, user.role
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")
    user.is_blocked = True
    await db.commit()
    await db.refresh(user, attribute_names=["is_blocked"])
    return serialize_user(user)


@router.post("/{user_id}/unblock", response_model=UserOut)
async def unblock_user(
    user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    user = await _load_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi")
    if not has_permission(current_user, _resource_for_role(user.role), "edit") or not _can_manage_target_role(
        current_user, user.role
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")
    user.is_blocked = False
    await db.commit()
    await db.refresh(user, attribute_names=["is_blocked"])
    return serialize_user(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi")
    if not has_permission(current_user, _resource_for_role(user.role), "delete") or not _can_manage_target_role(
        current_user, user.role
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")
    await db.delete(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu foydalanuvchi bildirishnomalarga bog'langan, o'chirib bo'lmaydi. Buning o'rniga bloklang.",
        ) from exc
