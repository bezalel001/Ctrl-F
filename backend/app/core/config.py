from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ctrl-F Backend"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", validation_alias="APP_ENV")
    jwt_secret: str = Field(default="change-me", validation_alias="JWT_SECRET")
    database_url: str = Field(
        default="sqlite:///./ctrlf.db",
        validation_alias="DATABASE_URL",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
