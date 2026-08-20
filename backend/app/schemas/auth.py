from pydantic import BaseModel, Field

from app.schemas.user import UserOut


class LoginRequest(BaseModel):
    username: str
    password: str
    captcha_token: str
    captcha_answer: str


class CaptchaResponse(BaseModel):
    captcha_token: str
    image: str


class TokenResponse(BaseModel):
    csrf_token: str
    user: UserOut


class MeResponse(BaseModel):
    csrf_token: str
    user: UserOut


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    username: str | None = Field(default=None, min_length=3, max_length=100)
    current_password: str | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=100)
