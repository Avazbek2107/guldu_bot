import argparse
import asyncio

from app.core.database import async_session_factory
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User


async def create_superadmin(username: str, password: str, full_name: str, phone: str) -> None:
    async with async_session_factory() as db:
        user = User(
            username=username,
            password_hash=hash_password(password),
            full_name=full_name,
            phone=phone,
            role=UserRole.SUPER_ADMIN,
            faculty_id=None,
        )
        db.add(user)
        await db.commit()
        print(f"Super admin '{username}' yaratildi (id={user.id})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Birinchi Super Admin hisobini yaratish")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--full-name", required=True, dest="full_name")
    parser.add_argument("--phone", required=True)
    args = parser.parse_args()

    asyncio.run(create_superadmin(args.username, args.password, args.full_name, args.phone))


if __name__ == "__main__":
    main()
