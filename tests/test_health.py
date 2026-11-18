from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from learning_platform.dependencies import get_db_session
from learning_platform.main import app


@pytest.fixture
async def client():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.mark.anyio
async def test_health_live(client: AsyncClient):
    response = await client.get("/health/live")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "live"}


@pytest.mark.anyio
async def test_health_ready_success(
    client: AsyncClient, mock_db_session: AsyncMock
):
    """Verify readiness succeeds (200) without requiring a live PostgreSQL instance

    by overriding the get_db_session dependency.
    """

    async def override_get_db_session():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    try:
        response = await client.get("/health/ready")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"status": "ready"}
        mock_db_session.execute.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_health_ready_database_unavailable(
    client: AsyncClient, mock_db_session: AsyncMock
):
    """Verify readiness returns 503 when the database execution fails."""
    mock_db_session.execute.side_effect = ConnectionRefusedError(
        "Database unreachable"
    )

    async def override_get_db_session():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    try:
        response = await client.get("/health/ready")
        assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
        assert response.json() == {
            "status": "unavailable",
            "detail": "Database unreachable",
        }
    finally:
        app.dependency_overrides.clear()
