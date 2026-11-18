from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from learning_platform.main import app


@pytest.fixture
async def client():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.mark.anyio
async def test_health_live(client: AsyncClient):
    response = await client.get("/health/live")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "live"}


@pytest.mark.anyio
async def test_health_ready_success(client: AsyncClient):
    response = await client.get("/health/ready")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ready"}


@pytest.mark.anyio
async def test_health_ready_database_unavailable(client: AsyncClient):
    with patch.object(
        AsyncSession, "execute", new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.side_effect = ConnectionRefusedError("Database unreachable")
        response = await client.get("/health/ready")
        assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
        assert response.json() == {
            "status": "unavailable",
            "detail": "Database unreachable",
        }
