from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.enums import OrgUnitType, UserRole
from app.models.faculty import Faculty
from app.models.user import User
from app.schemas.faculty import FacultyCreate, FacultyOut, FacultyUpdate

router = APIRouter(prefix="/faculties", tags=["faculties"])


@router.get("", response_model=list[FacultyOut])
async def list_faculties(
    unit_type: OrgUnitType | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(Faculty)
    if unit_type is not None:
        query = query.where(Faculty.unit_type == unit_type)
    result = await db.execute(query.order_by(Faculty.name))
    return result.scalars().all()


@router.post("", response_model=FacultyOut, status_code=status.HTTP_201_CREATED)
async def create_faculty(
    payload: FacultyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    faculty = Faculty(name=payload.name, unit_type=payload.unit_type)
    db.add(faculty)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu nomdagi fakultet/bo'lim allaqachon mavjud",
        ) from exc
    await db.refresh(faculty)
    return faculty


@router.patch("/{faculty_id}", response_model=FacultyOut)
async def update_faculty(
    faculty_id: int,
    payload: FacultyUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    faculty = await db.get(Faculty, faculty_id)
    if faculty is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fakultet/bo'lim topilmadi")
    faculty.name = payload.name
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu nomdagi fakultet/bo'lim allaqachon mavjud",
        ) from exc
    await db.refresh(faculty)
    return faculty
