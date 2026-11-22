from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from learning_platform.modules.courses.infrastructure.persistence.models.category_model import (
    CategoryModel,
)
from learning_platform.modules.courses.infrastructure.persistence.unit_of_work import (
    SqlAlchemyUnitOfWork,
)


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def unit_of_work(mock_session: AsyncMock) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(mock_session)


@pytest.mark.anyio
async def test_categories_repository_uses_shared_session(
    unit_of_work: SqlAlchemyUnitOfWork, mock_session: AsyncMock
):
    mock_session.get.return_value = None

    categories = unit_of_work.categories
    assert categories is unit_of_work.categories
    assert categories._session is mock_session
    assert await categories.get_by_id(42) is None

    mock_session.get.assert_awaited_once_with(CategoryModel, 42)


@pytest.mark.anyio
async def test_commit_and_rollback_delegate_to_session(
    unit_of_work: SqlAlchemyUnitOfWork, mock_session: AsyncMock
):
    await unit_of_work.commit()
    await unit_of_work.rollback()

    mock_session.commit.assert_awaited_once_with()
    mock_session.rollback.assert_awaited_once_with()


@pytest.mark.anyio
@pytest.mark.parametrize("operation", ["commit", "rollback"])
async def test_session_errors_propagate(
    operation: str,
    unit_of_work: SqlAlchemyUnitOfWork,
    mock_session: AsyncMock,
):
    failure = RuntimeError(f"{operation} failure")
    getattr(mock_session, operation).side_effect = failure

    with pytest.raises(RuntimeError) as exc_info:
        await getattr(unit_of_work, operation)()

    assert exc_info.value is failure
