from http import HTTPStatus
from unittest.mock import patch

from fastapi import APIRouter
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from learning_platform.dependencies import DbSession
from learning_platform.main import app

# Router used to verify the database session dependency
db_probe_router = APIRouter(prefix="/_test_db")
captured_session: AsyncSession | None = None


@db_probe_router.get("/session")
async def probe_session(session: DbSession):
    global captured_session
    captured_session = session
    return {"status": "ok", "session_type": type(session).__name__}


app.include_router(db_probe_router)


def test_application_starts_successfully():
    """Verify that TestClient entering its context manager triggers lifespan startup,

    populating app.state with the database engine and session factory.
    """
    with TestClient(app) as client:
        # Check that the lifespan startup populated state attributes
        assert hasattr(app.state, "db_engine")
        assert isinstance(app.state.db_engine, AsyncEngine)
        assert callable(app.state.session_factory)

        # Verify the application responds to requests
        response = client.get("/health/live")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"status": "live"}


def test_request_obtains_database_session_and_closes_after_request():
    """Verify that a request successfully obtains an AsyncSession via Depends(get_db_session)

    and that the session is closed when the request finishes.
    """
    global captured_session
    captured_session = None

    with (
        patch.object(
            AsyncSession, "close", autospec=True, side_effect=AsyncSession.close
        ) as mock_close,
        TestClient(app) as client,
    ):
        # Before the request, no session has been closed yet
        assert mock_close.call_count == 0

        response = client.get("/_test_db/session")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"status": "ok", "session_type": "AsyncSession"}

        # Verify that the route received a valid AsyncSession instance
        assert captured_session is not None
        assert isinstance(captured_session, AsyncSession)

        # Verify that close() was invoked once when the request finished
        assert mock_close.call_count == 1


def test_engine_is_disposed_during_application_shutdown():
    """Verify that exiting the TestClient context manager triggers lifespan shutdown

    and disposes of the SQLAlchemy AsyncEngine.
    """
    with patch.object(AsyncEngine, "dispose", autospec=True) as mock_dispose:
        with TestClient(app):
            # Engine should not be disposed while the application is active
            assert mock_dispose.call_count == 0

        # Lifespan shutdown should have awaited app.state.db_engine.dispose()
        assert mock_dispose.call_count == 1
