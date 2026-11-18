from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from learning_platform.modules.courses.domain.entities.category import Category
from learning_platform.modules.courses.infrastructure.persistence.models.category_model import (
    CategoryModel,
)
from learning_platform.modules.courses.infrastructure.persistence.repositories.sqlalchemy_category_repository import (
    SqlAlchemyCategoryRepository,
)


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session: AsyncMock):
    return SqlAlchemyCategoryRepository(mock_session)


def test_entity_to_model_conversion():
    entity = Category(name="Backend Development", description="Python and databases", id=10)
    model = SqlAlchemyCategoryRepository._to_model(entity)

    assert isinstance(model, CategoryModel)
    assert model.id == 10
    assert model.name == "Backend Development"
    assert model.description == "Python and databases"


def test_entity_to_model_conversion_without_id():
    entity = Category(name="Frontend Development", description="HTML, CSS, JS")
    model = SqlAlchemyCategoryRepository._to_model(entity)

    assert isinstance(model, CategoryModel)
    assert model.id is None
    assert model.name == "Frontend Development"
    assert model.description == "HTML, CSS, JS"


def test_model_to_entity_conversion():
    model = CategoryModel(id=5, name="Data Science", description="Machine Learning")
    entity = SqlAlchemyCategoryRepository._to_entity(model)

    assert isinstance(entity, Category)
    assert entity.id == 5
    assert entity.name == "Data Science"
    assert entity.description == "Machine Learning"


@pytest.mark.anyio
async def test_get_by_id_found(
    repository: SqlAlchemyCategoryRepository, mock_session: AsyncMock
):
    mock_model = CategoryModel(id=1, name="DevOps", description="Docker, K8s")
    mock_session.get.return_value = mock_model

    result = await repository.get_by_id(1)

    assert result is not None
    assert isinstance(result, Category)
    assert result.id == 1
    assert result.name == "DevOps"
    assert result.description == "Docker, K8s"
    mock_session.get.assert_awaited_once_with(CategoryModel, 1)


@pytest.mark.anyio
async def test_get_by_id_not_found(
    repository: SqlAlchemyCategoryRepository, mock_session: AsyncMock
):
    mock_session.get.return_value = None

    result = await repository.get_by_id(999)

    assert result is None
    mock_session.get.assert_awaited_once_with(CategoryModel, 999)


@pytest.mark.anyio
async def test_get_by_name_found(
    repository: SqlAlchemyCategoryRepository, mock_session: AsyncMock
):
    mock_model = CategoryModel(id=2, name="Cybersecurity", description="Network security")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_model
    mock_session.execute.return_value = mock_result

    result = await repository.get_by_name("Cybersecurity")

    assert result is not None
    assert isinstance(result, Category)
    assert result.id == 2
    assert result.name == "Cybersecurity"
    mock_session.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_get_by_name_not_found(
    repository: SqlAlchemyCategoryRepository, mock_session: AsyncMock
):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await repository.get_by_name("NonExistent")

    assert result is None
    mock_session.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_list_all(
    repository: SqlAlchemyCategoryRepository, mock_session: AsyncMock
):
    mock_models = [
        CategoryModel(id=1, name="Cat 1", description="Desc 1"),
        CategoryModel(id=2, name="Cat 2", description="Desc 2"),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_models
    mock_session.execute.return_value = mock_result

    result = await repository.list_all()

    assert len(result) == 2
    assert all(isinstance(c, Category) for c in result)
    assert result[0].id == 1
    assert result[0].name == "Cat 1"
    assert result[1].id == 2
    assert result[1].name == "Cat 2"


@pytest.mark.anyio
async def test_add_new_category(
    repository: SqlAlchemyCategoryRepository, mock_session: AsyncMock
):
    entity = Category(name="Cloud Computing", description="AWS and GCP")

    # When flush is called, simulate the database assigning an ID to the added model
    async def fake_flush():
        added_model = mock_session.add.call_args[0][0]
        added_model.id = 42

    mock_session.flush.side_effect = fake_flush

    await repository.add_category(entity)

    mock_session.add.assert_called_once()
    added_arg = mock_session.add.call_args[0][0]
    assert isinstance(added_arg, CategoryModel)
    assert added_arg.name == "Cloud Computing"
    assert added_arg.description == "AWS and GCP"
    mock_session.flush.assert_awaited_once()
    assert entity.id == 42


@pytest.mark.anyio
async def test_add_existing_category_updates_model(
    repository: SqlAlchemyCategoryRepository, mock_session: AsyncMock
):
    existing_model = CategoryModel(id=1, name="Old Name", description="Old Desc")
    mock_session.get.return_value = existing_model

    updated_entity = Category(name="New Name", description="New Desc", id=1)

    await repository.add_category(updated_entity)

    mock_session.get.assert_awaited_once_with(CategoryModel, 1)
    assert existing_model.name == "New Name"
    assert existing_model.description == "New Desc"
    mock_session.add.assert_not_called()


@pytest.mark.anyio
async def test_delete_existing_category(
    repository: SqlAlchemyCategoryRepository, mock_session: AsyncMock
):
    existing_model = CategoryModel(id=7, name="To Delete", description=None)
    mock_session.get.return_value = existing_model

    entity = Category(name="To Delete", id=7)

    await repository.delete(entity)

    mock_session.get.assert_awaited_once_with(CategoryModel, 7)
    mock_session.delete.assert_awaited_once_with(existing_model)
    mock_session.flush.assert_awaited_once()


@pytest.mark.anyio
async def test_delete_category_without_id_is_noop(
    repository: SqlAlchemyCategoryRepository, mock_session: AsyncMock
):
    entity = Category(name="Unsaved")

    await repository.delete(entity)

    mock_session.get.assert_not_called()
    mock_session.delete.assert_not_called()
