from pydantic import BaseModel

from app.schemas.user import UserOut


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    csrf_token: str
    user: UserOut


class MeResponse(BaseModel):
    csrf_token: str
    user: UserOut
