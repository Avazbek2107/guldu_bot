from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

DEFAULT_JWT_SECRET_KEY = "dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://guldu:guldu@localhost:5432/guldu_bot"
    storage_dir: str = "/app/storage"
    app_env: str = "development"

    jwt_secret_key: str = DEFAULT_JWT_SECRET_KEY
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    cors_origins: str = "http://localhost:5173"

    @model_validator(mode="after")
    def _check_production_secret(self) -> "Settings":
        if self.app_env == "production" and self.jwt_secret_key == DEFAULT_JWT_SECRET_KEY:
            raise ValueError(
                "JWT_SECRET_KEY production muhitida standart qiymatda qolishi mumkin emas. "
                "`openssl rand -hex 32` bilan yangi kalit generatsiya qiling."
            )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
