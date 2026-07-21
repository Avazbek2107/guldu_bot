from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://guldu:guldu@localhost:5432/guldu_bot"
    storage_dir: str = "/app/storage"
    app_env: str = "development"


settings = Settings()
