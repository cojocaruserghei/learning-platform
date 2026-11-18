from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession]:
    """Dependency that manages the database session lifecycle per HTTP request.

    1. Retrieves the session factory from request.app.state.
    2. Creates an AsyncSession.
    3. Yields the session to the caller.
    4. Closes the session upon request completion without committing.
    """
    session_factory: async_sessionmaker[AsyncSession] = (
        request.app.state.session_factory
    )

    async with session_factory() as session:
        yield session


# Type alias for clean FastAPI endpoint signatures
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
