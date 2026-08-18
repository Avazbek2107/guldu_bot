from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, has_permission
from app.core.database import get_db
from app.models.enums import OrgUnitType
from app.models.faculty import Faculty
from app.models.user import User
from app.schemas.faculty import (
    FacultyCreate,
    FacultyImportResult,
    FacultyImportSkip,
    FacultyOut,
    FacultyUpdate,
)
from app.services.faculty_excel import generate_faculty_xlsx, parse_faculty_rows

router = APIRouter(prefix="/faculties", tags=["faculties"])


def _resource_for_unit_type(unit_type: OrgUnitType) -> str:
    return "departments" if unit_type == OrgUnitType.DEPARTMENT else "faculties"


def _require_permission(current_user: User, unit_type: OrgUnitType, action: str) -> None:
    if not has_permission(current_user, _resource_for_unit_type(unit_type), action):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu amal uchun ruxsatingiz yo'q")


@router.get("", response_model=list[FacultyOut])
async def list_faculties(
    unit_type: OrgUnitType | None = None,
    parent_id: int | None = None,
    top_level: bool | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(Faculty)
    if unit_type is not None:
        query = query.where(Faculty.unit_type == unit_type)
    if parent_id is not None:
        query = query.where(Faculty.parent_id == parent_id)
    if top_level:
        query = query.where(Faculty.parent_id.is_(None))
    result = await db.execute(query.order_by(Faculty.name))
    return result.scalars().all()


@router.get("/export")
async def export_faculties(
    unit_type: OrgUnitType | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_permission(current_user, unit_type or OrgUnitType.FACULTY, "view")
    query = select(Faculty)
    if unit_type is not None:
        query = query.where(Faculty.unit_type == unit_type)
    faculties = (await db.execute(query.order_by(Faculty.name))).scalars().all()

    content = generate_faculty_xlsx(faculties)
    filename = "bolimlar.xlsx" if unit_type == OrgUnitType.DEPARTMENT else "fakultetlar.xlsx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/import", response_model=FacultyImportResult)
async def import_faculties(
    unit_type: OrgUnitType = OrgUnitType.FACULTY,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_permission(current_user, unit_type, "create")
    content = await file.read()
    try:
        rows = parse_faculty_rows(content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Fayl formatini o'qib bo'lmadi"
        ) from exc

    existing = (await db.execute(select(Faculty.name))).scalars().all()
    existing_names = {name.strip().lower() for name in existing}

    created = 0
    skipped: list[FacultyImportSkip] = []
    for row in rows:
        key = row.name.strip().lower()
        if key in existing_names:
            skipped.append(FacultyImportSkip(row=row.row_number, reason=f"Allaqachon mavjud: '{row.name}'"))
            continue
        db.add(Faculty(name=row.name, unit_type=unit_type))
        existing_names.add(key)
        created += 1

    await db.commit()
    return FacultyImportResult(created=created, skipped=skipped)


@router.post("", response_model=FacultyOut, status_code=status.HTTP_201_CREATED)
async def create_faculty(
    payload: FacultyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_permission(current_user, payload.unit_type, "create")

    parent: Faculty | None = None
    if payload.parent_id is not None:
        parent = await db.get(Faculty, payload.parent_id)
        if parent is None or parent.unit_type != OrgUnitType.FACULTY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kafedra faqat fakultetga biriktirilishi mumkin",
            )

    faculty = Faculty(name=payload.name, unit_type=payload.unit_type, parent_id=payload.parent_id)
    db.add(faculty)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu nomdagi fakultet/bo'lim/kafedra allaqachon mavjud",
        ) from exc
    await db.refresh(faculty)
    return faculty


@router.patch("/{faculty_id}", response_model=FacultyOut)
async def update_faculty(
    faculty_id: int,
    payload: FacultyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    faculty = await db.get(Faculty, faculty_id)
    if faculty is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fakultet/bo'lim topilmadi")
    _require_permission(current_user, faculty.unit_type, "edit")
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


@router.delete("/{faculty_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faculty(
    faculty_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    faculty = await db.get(Faculty, faculty_id)
    if faculty is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fakultet/bo'lim topilmadi")
    _require_permission(current_user, faculty.unit_type, "delete")
    await db.delete(faculty)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bunga bog'liq xodimlar, arizalar yoki inventar mavjud, avval ularni boshqa "
            "fakultet/kafedraga ko'chiring",
        ) from exc
