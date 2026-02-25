import logging
import secrets
import re
from typing import Any
from pathlib import Path

from pydantic import AnyHttpUrl, PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

level = logging.INFO

class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    BASEDIR: Path = Path(__file__).parent.resolve()

    API_STR: str
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 180  # 180 days
    SERVER_NAME: str = "localhost"
    SERVER_HOST: AnyHttpUrl = "https://localhost"
    BACKEND_CORS_ORIGINS: Any = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: PostgresDsn | str | None = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, values: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v

        return PostgresDsn.build(
            scheme="postgresql",
            username=values.data.get("POSTGRES_USER"),
            password=values.data.get("POSTGRES_PASSWORD"),
            host=values.data.get("POSTGRES_SERVER"),
            path=f"{values.data.get('POSTGRES_DB') or ''}",
        ).unicode_string()

    SQLALCHEMY_ASYNC_DATABASE_URI: PostgresDsn | str | None = None

    @field_validator("SQLALCHEMY_ASYNC_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_async_connection(cls, v: str | None, values: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v

        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.data.get("POSTGRES_USER"),
            password=values.data.get("POSTGRES_PASSWORD"),
            host=values.data.get("POSTGRES_SERVER"),
            path=f"{values.data.get('POSTGRES_DB') or ''}",
        ).unicode_string()
        # postgresql+asyncpg://postgres:password@localhost:25432/postgres

    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str

    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None

    REDIS_URL: str
    CACHE_TTL: int

    S3_SERVICE_NAME: str | None = None
    S3_ENDPOINTS_URL: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_BUCKET_NAME: str | None = None

    tel_pattern: str = r"^\+?\d{10,14}$"

    gsms_token: str ='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiQVhBUyIsImlhdCI6MTc0NDIwMTU1OCwiaXNzIjoiYXBpLmdyZWVuc21zLnJ1In0.ltH3-QfqdpTJ7MCJWR2MPpbrCpkNj3_J11_wHbIOCHY'

settings = Settings()
