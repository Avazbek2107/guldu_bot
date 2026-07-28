import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/storage", tags=["storage"])


def _serve(subdir: str, filename: str) -> FileResponse:
    if os.path.basename(filename) != filename or filename in ("", ".", ".."):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Noto'g'ri fayl nomi")
    path = os.path.join(settings.storage_dir, subdir, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fayl topilmadi")
    return FileResponse(path)


@router.get("/avatars/{filename}")
async def get_avatar(filename: str, current_user: User = Depends(get_current_user)) -> FileResponse:
    return _serve("avatars", filename)


@router.get("/ticket_attachments/{filename}")
async def get_ticket_attachment(filename: str, current_user: User = Depends(get_current_user)) -> FileResponse:
    return _serve("ticket_attachments", filename)
