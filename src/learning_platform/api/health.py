from http import HTTPStatus

import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from learning_platform.dependencies import DbSession

router = APIRouter(tags=["Health"])
logger = structlog.get_logger(__name__)


@router.get("/health/live")
async def health():
    logger.info("Health live called")
    return {"status": "live"}


@router.get("/health/ready")
async def health_ready(session: DbSession):
    logger.info("Health ready called")
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        logger.error("Database health check failed", exc_info=exc)
        return JSONResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "detail": "Database unreachable"},
        )
