from unittest.mock import AsyncMock

import pytest

from learning_platform.modules.courses.application.services.category_service import (
    CategoryService,
)
from learning_platform.modules.courses.domain.entities.category import Category
from learning_platform.modules.courses.domain.repositories.category_repository import (
    ICategoryRepository,
)


class InMemoryCategoryRepository(ICategoryRepository):
    """In-memory test double verifying that CategoryService operates

    independently of SQLAlchemy / AsyncSession.
    """

    def __init__(self) -> None:
        self._storage: dict[int, Category] = {}
        self._next_id: int = 1

    async def add_category(self, category: Category) -> None:
        if category.id is None:
            category.id = self._next_id
            self._next_id += 1
        self._storage[category.id] = category

    async def delete(self, category: Category) -> None:
        if category.id is not None and category.id in self._storage:
            del self._storage[category.id]

    async def get_by_id(self, category_id: int) -> Category | None:
        return self._storage.get(category_id)

    async def get_by_name(self, name: str) -> Category | None:
        for cat in self._storage.values():
            if cat.name == name:
                return cat
        return None

    async def list_all(self) -> list[Category]:
        return list(self._storage.values())


@pytest.fixture
def in_memory_repo():
    return InMemoryCategoryRepository()


@pytest.fixture
def service(in_memory_repo: InMemoryCategoryRepository):
    return CategoryService(in_memory_repo)


@pytest.mark.anyio
async def test_create_category_success(service: CategoryService):
    category = await service.create_category(
        name="Data Engineering", description="Pipelines & ETL"
    )

    assert isinstance(category, Category)
    assert category.id is not None
    assert category.name == "Data Engineering"
    assert category.description == "Pipelines & ETL"


@pytest.mark.anyio
async def test_create_category_duplicate_name_raises_error(
    service: CategoryService,
):
    await service.create_category(name="Web Development")

    with pytest.raises(ValueError, match="already exists"):
        await service.create_category(name="Web Development")


@pytest.mark.anyio
async def test_create_category_invalid_name_raises_error(
    service: CategoryService,
):
    with pytest.raises(ValueError, match="cannot be empty"):
        await service.create_category(name="   ")


@pytest.mark.anyio
async def test_get_category_by_id_found(service: CategoryService):
    created = await service.create_category(name="Mobile Dev")

    found = await service.get_category_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.name == "Mobile Dev"


@pytest.mark.anyio
async def test_get_category_by_id_not_found(service: CategoryService):
    result = await service.get_category_by_id(999)
    assert result is None


@pytest.mark.anyio
async def test_list_categories(service: CategoryService):
    await service.create_category(name="AI / ML")
    await service.create_category(name="Security")

    categories = await service.list_categories()

    assert len(categories) == 2
    names = [c.name for c in categories]
    assert "AI / ML" in names
    assert "Security" in names


@pytest.mark.anyio
async def test_service_uses_mock_repository():
    mock_repo = AsyncMock(spec=ICategoryRepository)
    mock_repo.get_by_name.return_value = None
    mock_service = CategoryService(mock_repo)

    result = await mock_service.create_category(
        name="Rust", description="Systems programming"
    )

    assert result.name == "Rust"
    mock_repo.get_by_name.assert_awaited_once_with("Rust")
    mock_repo.add_category.assert_awaited_once()
