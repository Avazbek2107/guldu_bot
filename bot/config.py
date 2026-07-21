from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = ""
    escalation_check_interval_seconds: int = 60
    escalation_backup_after_minutes: int = 30


settings = BotSettings()
