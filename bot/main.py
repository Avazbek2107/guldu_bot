import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.database import async_session_factory

from bot.config import settings
from bot.handlers import registration, technician, tickets
from bot.middlewares.activity import ActivityTrackingMiddleware
from bot.services.escalation import run_escalation_loop

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(ActivityTrackingMiddleware())

    dp.include_router(registration.router)
    dp.include_router(tickets.router)
    dp.include_router(technician.router)

    escalation_task = asyncio.create_task(
        run_escalation_loop(
            bot,
            async_session_factory,
            settings.escalation_check_interval_seconds,
            settings.escalation_backup_after_minutes,
        )
    )

    try:
        await dp.start_polling(bot)
    finally:
        escalation_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
