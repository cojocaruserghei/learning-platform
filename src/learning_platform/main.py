from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from learning_platform.api import health
from learning_platform.config import get_settings
from learning_platform.shared.infrastructure.persistence.database import (
    create_db_engine,
)
from learning_platform.shared.infrastructure.persistence.session import (
    create_session_factory,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # 1. Create engine and session factory at startup
    engine: AsyncEngine = create_db_engine(settings)
    session_factory: async_sessionmaker[AsyncSession] = create_session_factory(
        engine
    )

    # 2. Store both in app.state
    app.state.db_engine = engine
    app.state.session_factory = session_factory
    app.state.settings = settings

    try:
        yield
    finally:
        # 3. Dispose of that same engine on shutdown
        await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="Learning Platform",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(health.router)
