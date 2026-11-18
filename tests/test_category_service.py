import pytest

from learning_platform.modules.courses.application.services.category_service import (
    CategoryService,
)
from learning_platform.modules.courses.domain.entities.category import Category
from learning_platform.modules.courses.domain.repositories.category_repository import (
    ICategoryRepository,
)


class InMemoryCategoryRepository(ICategoryRepository):
    """In-memory fake repository implementation for fast, isolated unit tests.

    Runs entirely without PostgreSQL or network connections.
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
def fake_repo() -> InMemoryCategoryRepository:
    return InMemoryCategoryRepository()


@pytest.fixture
def service(fake_repo: InMemoryCategoryRepository) -> CategoryService:
    return CategoryService(fake_repo)


# ============================================================================
# 1. Category Creation Tests
# ============================================================================


@pytest.mark.anyio
async def test_create_category_success(service: CategoryService):
    """Verify standard category creation with valid name and description."""
    category = await service.create_category(
        name="Data Engineering",
        description="Pipelines, ETL, and data warehouses",
    )

    assert isinstance(category, Category)
    assert category.id == 1
    assert category.name == "Data Engineering"
    assert category.description == "Pipelines, ETL, and data warehouses"


@pytest.mark.anyio
async def test_create_category_without_description(service: CategoryService):
    """Verify category creation succeeds when description is omitted."""
    category = await service.create_category(name="Machine Learning")

    assert category.id is not None
    assert category.name == "Machine Learning"
    assert category.description is None


@pytest.mark.anyio
async def test_create_category_strips_surrounding_whitespace(
    service: CategoryService,
):
    """Verify category names are trimmed of leading/trailing whitespace."""
    category = await service.create_category(name="   DevOps   ")

    assert category.name == "DevOps"


# ============================================================================
# 2. Empty Category Names Tests
# ============================================================================


@pytest.mark.anyio
async def test_create_category_with_empty_string_raises_error(
    service: CategoryService,
):
    """Verify empty string category names are rejected."""
    with pytest.raises(
        ValueError, match="Category name cannot be empty or whitespace"
    ):
        await service.create_category(name="")


@pytest.mark.anyio
async def test_create_category_with_whitespace_only_raises_error(
    service: CategoryService,
):
    """Verify whitespace-only category names are rejected."""
    with pytest.raises(
        ValueError, match="Category name cannot be empty or whitespace"
    ):
        await service.create_category(name="   \t\n  ")


# ============================================================================
# 3. Invalid Category Names Tests
# ============================================================================


@pytest.mark.anyio
async def test_create_category_with_name_exceeding_max_length_raises_error(
    service: CategoryService,
):
    """Verify category names longer than 100 characters are rejected."""
    long_name = "A" * 101
    with pytest.raises(
        ValueError, match="Category name cannot exceed 100 characters"
    ):
        await service.create_category(name=long_name)


@pytest.mark.anyio
async def test_create_category_with_non_string_name_raises_type_error(
    service: CategoryService,
):
    """Verify non-string types for category name raise TypeError."""
    with pytest.raises(TypeError, match="Category name must be a string"):
        # Intentionally passing an invalid type
        await service.create_category(name=12345)  # type: ignore[arg-type]


@pytest.mark.anyio
async def test_create_category_with_none_name_raises_type_error(
    service: CategoryService,
):
    """Verify None for category name raises TypeError."""
    with pytest.raises(TypeError, match="Category name must be a string"):
        await service.create_category(name=None)  # type: ignore[arg-type]


@pytest.mark.anyio
async def test_create_category_with_duplicate_name_raises_error(
    service: CategoryService,
):
    """Verify duplicate category names are rejected."""
    await service.create_category(name="Cloud Computing")

    with pytest.raises(
        ValueError, match="Category with name 'Cloud Computing' already exists"
    ):
        await service.create_category(name="Cloud Computing")


# ============================================================================
# 4. Getting a Category Tests
# ============================================================================


@pytest.mark.anyio
async def test_get_category_by_id_found(service: CategoryService):
    """Verify retrieving an existing category by ID."""
    created = await service.create_category(
        name="Security", description="AppSec & Pentesting"
    )

    found = await service.get_category_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.name == "Security"
    assert found.description == "AppSec & Pentesting"


@pytest.mark.anyio
async def test_get_category_by_id_not_found_returns_none(
    service: CategoryService,
):
    """Verify retrieving a non-existent category ID returns None."""
    result = await service.get_category_by_id(999)
    assert result is None


# ============================================================================
# 5. Listing Categories Tests
# ============================================================================


@pytest.mark.anyio
async def test_list_categories_empty(service: CategoryService):
    """Verify listing categories when none have been created returns an empty list."""
    categories = await service.list_categories()
    assert categories == []


@pytest.mark.anyio
async def test_list_categories_returns_all_items(service: CategoryService):
    """Verify listing categories returns all saved categories."""
    cat1 = await service.create_category(name="Frontend")
    cat2 = await service.create_category(name="Backend")
    cat3 = await service.create_category(name="DevOps")

    categories = await service.list_categories()

    assert len(categories) == 3
    ids = [c.id for c in categories]
    names = [c.name for c in categories]

    assert ids == [cat1.id, cat2.id, cat3.id]
    assert names == ["Frontend", "Backend", "DevOps"]
