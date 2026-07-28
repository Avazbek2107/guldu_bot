import os
import uuid

from aiogram.types import Message

from app.core.config import settings as backend_settings


async def save_telegram_file(message: Message, file_id: str, extension: str) -> str:
    os.makedirs(backend_settings.storage_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"
    destination = os.path.join(backend_settings.storage_dir, filename)
    await message.bot.download(file_id, destination=destination)
    return destination


async def save_closing_attachment(message: Message, file_id: str, extension: str) -> str:
    subdir = "ticket_attachments"
    directory = os.path.join(backend_settings.storage_dir, subdir)
    os.makedirs(directory, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"
    destination = os.path.join(directory, filename)
    await message.bot.download(file_id, destination=destination)
    return f"{subdir}/{filename}"
