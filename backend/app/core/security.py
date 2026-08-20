import secrets
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

import bcrypt
import jwt

from app.core.config import settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


class IssuedToken(NamedTuple):
    token: str
    csrf_token: str


def create_access_token(user_id: int, role: str) -> IssuedToken:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    csrf_token = secrets.token_urlsafe(32)
    payload = {"sub": str(user_id), "role": role, "csrf": csrf_token, "exp": expire}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return IssuedToken(token=token, csrf_token=csrf_token)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def create_captcha_token(jti: str, code_hash: str, expire_minutes: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {"typ": "captcha", "jti": jti, "code_hash": code_hash, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_captcha_token(token: str) -> dict:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("typ") != "captcha":
        raise jwt.InvalidTokenError("Yaroqsiz captcha token")
    return payload
