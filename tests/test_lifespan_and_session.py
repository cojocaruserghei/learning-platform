from http import HTTPStatus
from unittest.mock import patch

from fastapi import APIRouter
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from learning_platform.dependencies import DbSession
from learning_platform.main import app
from learning_platform.shared.infrastructure.persistence import database

# Probe router to test the database session dependency during HTTP requests
db_probe_router = APIRouter(prefix="/_test_db")
captured_session: AsyncSession | None = None


@db_probe_router.get("/session")
async def probe_session(session: DbSession):
    global captured_session
    captured_session = session
    return {"status": "ok", "session_type": type(session).__name__}


app.include_router(db_probe_router)


def test_database_module_does_not_create_engine_at_import():
    """Verify database.py exposes create_db_engine rather than creating an engine at import."""
    assert hasattr(database, "create_db_engine")
    assert callable(database.create_db_engine)
    assert not hasattr(database, "engine")


def test_engine_creation_during_startup():
    """1. Verify engine creation during application startup (lifespan)."""
    with (
        patch(
            "learning_platform.main.create_db_engine",
            wraps=database.create_db_engine,
        ) as spy_create_engine,
        TestClient(app),
    ):
        # Engine factory should have been called once during startup
        assert spy_create_engine.call_count == 1

        # app.state.db_engine must be an active AsyncEngine
        assert hasattr(app.state, "db_engine")
        assert isinstance(app.state.db_engine, AsyncEngine)


def test_session_factory_availability_in_app_state():
    """2. Verify session factory availability and configuration in app.state."""
    with TestClient(app):
        # Session factory must be present in app.state
        assert hasattr(app.state, "session_factory")
        session_factory = app.state.session_factory
        assert isinstance(session_factory, async_sessionmaker)

        # Factory should produce an AsyncSession bound to the app's engine
        session = session_factory()
        assert isinstance(session, AsyncSession)
        assert session.bind == app.state.db_engine


def test_session_cleanup_after_request():
    """3. Verify database session is created for a request and cleaned up (closed) afterwards."""
    global captured_session
    captured_session = None

    with (
        patch.object(
            AsyncSession, "close", autospec=True, side_effect=AsyncSession.close
        ) as mock_close,
        TestClient(app) as client,
    ):
        # No session should be closed before the request
        assert mock_close.call_count == 0

        response = client.get("/_test_db/session")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"status": "ok", "session_type": "AsyncSession"}

        # Route received a valid AsyncSession
        assert captured_session is not None
        assert isinstance(captured_session, AsyncSession)

        # Session close() was awaited exactly once after the request completed
        assert mock_close.call_count == 1


def test_engine_disposal_during_shutdown():
    """4. Verify engine disposal during application shutdown (lifespan cleanup)."""
    with patch.object(AsyncEngine, "dispose", autospec=True) as mock_dispose:
        with TestClient(app):
            # Engine must NOT be disposed while the application is running
            assert mock_dispose.call_count == 0

        # Lifespan shutdown must have awaited engine.dispose()
        assert mock_dispose.call_count == 1
