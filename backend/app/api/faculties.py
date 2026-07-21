from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.faculty import Faculty
from app.models.user import User
from app.schemas.faculty import AssignTechnicianRequest, FacultyCreate, FacultyOut, FacultyUpdate

router = APIRouter(prefix="/faculties", tags=["faculties"])


@router.get("", response_model=list[FacultyOut])
async def list_faculties(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    result = await db.execute(select(Faculty).order_by(Faculty.name))
    return result.scalars().all()


@router.post("", response_model=FacultyOut, status_code=status.HTTP_201_CREATED)
async def create_faculty(
    payload: FacultyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    faculty = Faculty(name=payload.name)
    db.add(faculty)
    await db.commit()
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fakultet topilmadi")
    faculty.name = payload.name
    await db.commit()
    await db.refresh(faculty)
    return faculty


@router.post("/{faculty_id}/technicians", status_code=status.HTTP_204_NO_CONTENT)
async def assign_technician(
    faculty_id: int,
    payload: AssignTechnicianRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    faculty = await db.get(Faculty, faculty_id)
    if faculty is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fakultet topilmadi")

    technician = await db.get(User, payload.user_id)
    if technician is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi")

    new_role = UserRole(payload.role)

    if new_role == UserRole.TECHNICIAN_MAIN:
        result = await db.execute(
            select(User).where(
                User.faculty_id == faculty_id,
                User.role == UserRole.TECHNICIAN_MAIN,
                User.id != technician.id,
            )
        )
        current_main = result.scalar_one_or_none()
        if current_main is not None:
            current_main.role = UserRole.TECHNICIAN_BACKUP

    technician.faculty_id = faculty_id
    technician.role = new_role

    await db.commit()
