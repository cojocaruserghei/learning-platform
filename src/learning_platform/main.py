from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from learning_platform.api import health
from learning_platform.config import get_settings
from learning_platform.shared.infrastructure.persistence import database
from learning_platform.shared.infrastructure.persistence.session import (
    async_session_factory,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:

    engine: AsyncEngine = database.engine
    app.state.db_engine = engine
    app.state.session_factory = async_session_factory
    app.state.settings = settings

    try:
        yield
    finally:
        await app.state.db_engine.dispose()

app = FastAPI(
    title="Learning Platform",
    description="Learning Platform",
    version="1.0.0",
    debug=True,
    lifespan=lifespan,
)
settings = get_settings()
app.state.settings = settings

app.include_router(health.router)
web_api_router = APIRouter()
app.include_router(web_api_router, prefix=settings.api_v1_prefix)

