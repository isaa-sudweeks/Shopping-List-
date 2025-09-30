"""Application settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite+pysqlite:///./shopping.db"
    testing: bool = False

    model_config = SettingsConfigDict(env_prefix="SHOPPING_", env_file=".env", env_file_encoding="utf-8")


settings = Settings()
