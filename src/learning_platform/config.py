from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    app_name: str = "Learning Platform"
    app_env: Literal["development", "testing", "production"] = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    secret_key: str = ""
    postgres_db: str = "learning_platform"
    postgres_user: str = "admin"
    postgres_password: str = "admin"
    postgres_port: str = "5432"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
