import asyncio

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.faculty import Faculty

FACULTY_COUNT = 9


async def seed_faculties() -> None:
    async with async_session_factory() as db:
        result = await db.execute(select(Faculty.name))
        existing_names = set(result.scalars().all())

        created = 0
        for i in range(1, FACULTY_COUNT + 1):
            name = f"{i}-fakultet"
            if name not in existing_names:
                db.add(Faculty(name=name))
                created += 1

        await db.commit()
        print(f"{created} ta fakultet qo'shildi (jami {FACULTY_COUNT} ta bo'lishi kerak)")


if __name__ == "__main__":
    asyncio.run(seed_faculties())
