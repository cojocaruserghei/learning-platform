import pytest

from learning_platform.modules.courses.application.services.category_service import (
    CategoryService,
)
from learning_platform.modules.courses.domain.entities.category import Category
from learning_platform.modules.courses.domain.repositories.category_repository import (
    ICategoryRepository,
)
from learning_platform.modules.courses.domain.repositories.unit_of_work import (
    IUnitOfWork,
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

    async def update_category(self, category: Category) -> None:
        if category.id is not None and category.id in self._storage:
            self._storage[category.id] = category

    async def delete(self, category_id: int) -> None:
        if category_id in self._storage:
            del self._storage[category_id]

    async def get_by_id(self, category_id: int) -> Category | None:
        return self._storage.get(category_id)

    async def get_by_name(self, name: str) -> Category | None:
        for cat in self._storage.values():
            if cat.name == name:
                return cat
        return None

    async def list_all(self) -> list[Category]:
        return list(self._storage.values())


class FakeUnitOfWork(IUnitOfWork):
    def __init__(self, categories: InMemoryCategoryRepository) -> None:
        self._categories = categories
        self.commit_count = 0
        self.rollback_count = 0
        self.commit_error: Exception | None = None

    @property
    def categories(self) -> ICategoryRepository:
        return self._categories

    async def commit(self) -> None:
        self.commit_count += 1
        if self.commit_error is not None:
            raise self.commit_error

    async def rollback(self) -> None:
        self.rollback_count += 1


@pytest.fixture
def fake_repo() -> InMemoryCategoryRepository:
    return InMemoryCategoryRepository()


@pytest.fixture
def fake_uow(fake_repo: InMemoryCategoryRepository) -> FakeUnitOfWork:
    return FakeUnitOfWork(fake_repo)


@pytest.fixture
def service(fake_uow: FakeUnitOfWork) -> CategoryService:
    return CategoryService(fake_uow)


# ============================================================================
# 1. Category Creation Tests
# ============================================================================


@pytest.mark.anyio
async def test_create_category_success(
    service: CategoryService, fake_uow: FakeUnitOfWork
):
    """Verify standard category creation with valid name and description."""
    category = await service.create_category(
        name="Data Engineering",
        description="Pipelines, ETL, and data warehouses",
    )

    assert isinstance(category, Category)
    assert category.id == 1
    assert category.name == "Data Engineering"
    assert category.description == "Pipelines, ETL, and data warehouses"
    assert fake_uow.commit_count == 1
    assert fake_uow.rollback_count == 0


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
# 4. Update Category Tests
# ============================================================================


@pytest.mark.anyio
async def test_update_category_success(
    service: CategoryService, fake_uow: FakeUnitOfWork
):
    """Verify updating category name and description."""
    created = await service.create_category(
        name="Old Name", description="Old Desc"
    )

    updated = await service.update_category(
        category_id=created.id,
        name="New Name",
        description="New Desc",
    )

    assert updated is not None
    assert updated.id == created.id
    assert updated.name == "New Name"
    assert updated.description == "New Desc"

    # Verify persisted state
    found = await service.get_category_by_id(created.id)
    assert found is not None
    assert found.name == "New Name"
    assert found.description == "New Desc"
    assert fake_uow.commit_count == 2
    assert fake_uow.rollback_count == 0


@pytest.mark.anyio
@pytest.mark.parametrize("operation", ["create", "update"])
async def test_write_repository_failure_rolls_back_and_propagates(
    operation: str,
    service: CategoryService,
    fake_repo: InMemoryCategoryRepository,
    fake_uow: FakeUnitOfWork,
):
    if operation == "update":
        category = await service.create_category(name="Existing")
        fake_uow.commit_count = 0

    failure = RuntimeError("repository failure")

    async def fail_write(_category: Category) -> None:
        raise failure

    method_name = "add_category" if operation == "create" else "update_category"
    setattr(fake_repo, method_name, fail_write)

    with pytest.raises(RuntimeError) as exc_info:
        if operation == "create":
            await service.create_category(name="New")
        else:
            await service.update_category(category.id, name="Updated")

    assert exc_info.value is failure
    assert fake_uow.commit_count == 0
    assert fake_uow.rollback_count == 1


@pytest.mark.anyio
@pytest.mark.parametrize("operation", ["create", "update"])
async def test_commit_failure_rolls_back_and_propagates(
    operation: str,
    service: CategoryService,
    fake_uow: FakeUnitOfWork,
):
    if operation == "update":
        category = await service.create_category(name="Existing")
        fake_uow.commit_count = 0

    failure = RuntimeError("commit failure")
    fake_uow.commit_error = failure

    with pytest.raises(RuntimeError) as exc_info:
        if operation == "create":
            await service.create_category(name="New")
        else:
            await service.update_category(category.id, name="Updated")

    assert exc_info.value is failure
    assert fake_uow.commit_count == 1
    assert fake_uow.rollback_count == 1


@pytest.mark.anyio
async def test_non_writing_paths_do_not_commit_or_roll_back(
    service: CategoryService, fake_uow: FakeUnitOfWork
):
    with pytest.raises(ValueError):
        await service.create_category(name="")
    assert fake_uow.commit_count == 0
    assert fake_uow.rollback_count == 0

    first = await service.create_category(name="Python")
    second = await service.create_category(name="Java")
    with pytest.raises(ValueError, match="already exists"):
        await service.create_category(name="Python")
    with pytest.raises(ValueError, match="already exists"):
        await service.update_category(second.id, name="Python")
    with pytest.raises(ValueError):
        await service.update_category(first.id, name="")

    assert await service.update_category(999, name="Missing") is None
    assert await service.get_category_by_id(first.id) is first
    assert len(await service.list_categories()) == 2
    assert fake_uow.commit_count == 2
    assert fake_uow.rollback_count == 0


@pytest.mark.anyio
async def test_update_category_not_found_returns_none(
    service: CategoryService,
):
    """Verify updating a non-existent category returns None."""
    result = await service.update_category(
        category_id=999,
        name="Doesn't Exist",
    )
    assert result is None


@pytest.mark.anyio
async def test_update_category_duplicate_name_raises_error(
    service: CategoryService,
):
    """Verify updating a category to a name that already belongs to another category raises ValueError."""
    await service.create_category(name="Python")
    cat2 = await service.create_category(name="Java")

    with pytest.raises(
        ValueError, match="Category with name 'Python' already exists"
    ):
        await service.update_category(category_id=cat2.id, name="Python")


@pytest.mark.anyio
async def test_update_category_same_name_does_not_raise(
    service: CategoryService,
):
    """Verify updating description without changing name does not trigger uniqueness conflict."""
    cat = await service.create_category(name="Go", description="Original desc")

    updated = await service.update_category(
        category_id=cat.id,
        name="Go",
        description="Updated desc",
    )

    assert updated is not None
    assert updated.description == "Updated desc"


@pytest.mark.anyio
async def test_update_category_invalid_name_raises_error(
    service: CategoryService,
):
    """Verify updating category with empty name triggers domain validation error."""
    cat = await service.create_category(name="Valid")

    with pytest.raises(
        ValueError, match="Category name cannot be empty or whitespace"
    ):
        await service.update_category(category_id=cat.id, name="")


# ============================================================================
# 5. Getting a Category Tests
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
# 6. Listing Categories Tests
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
