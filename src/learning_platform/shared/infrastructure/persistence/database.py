from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from learning_platform.config import AppSettings, get_settings


def create_db_connection_string(settings: AppSettings) -> URL:
    return URL.create(
        drivername="postgresql+asyncpg",
        username=settings.postgres_user,
        password=settings.postgres_password,  # Automatically URL-encoded
        host="localhost",
        port=int(settings.postgres_port),
        database=settings.postgres_db,
    )


def create_db_engine(settings: AppSettings | None = None) -> AsyncEngine:
    if settings is None:
        settings = get_settings()

    return create_async_engine(
        create_db_connection_string(settings),
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
        echo=settings.debug,
    )
