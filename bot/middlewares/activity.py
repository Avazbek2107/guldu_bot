from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlalchemy import update

from app.core.database import async_session_factory
from app.models.user import User


class ActivityTrackingMiddleware(BaseMiddleware):
    """Stamps `User.last_bot_activity_at` on every message/button-tap from a
    registered user, so admins can see who's actually still using the bot —
    not just who registered once. A single UPDATE ... WHERE telegram_id = ...
    is a no-op if nobody's registered under that id yet, so it's safe to run
    unconditionally ahead of the real handler."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_id = None
        if isinstance(event, Update):
            source = event.message or event.callback_query
            if source is not None and source.from_user is not None:
                telegram_id = source.from_user.id

        if telegram_id is not None:
            async with async_session_factory() as db:
                await db.execute(
                    update(User)
                    .where(User.telegram_id == telegram_id)
                    .values(last_bot_activity_at=datetime.now(timezone.utc))
                )
                await db.commit()

        return await handler(event, data)
