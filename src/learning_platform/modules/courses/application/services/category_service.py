from learning_platform.modules.courses.domain.entities.category import Category
from learning_platform.modules.courses.domain.repositories.category_repository import (
    ICategoryRepository,
)


class CategoryService:
    """Application service coordinating operations on categories.

    Depends strictly on the ICategoryRepository abstraction, decoupled from
    any persistence framework or AsyncSession.
    """

    def __init__(self, repository: ICategoryRepository) -> None:
        self._repository = repository

    async def create_category(
        self, name: str, description: str | None = None
    ) -> Category:
        """Create and persist a new category.

        Validates domain entity rules and ensures name uniqueness.
        """
        category = Category(name=name, description=description)

        existing = await self._repository.get_by_name(category.name)
        if existing is not None:
            raise ValueError(f"Category with name '{category.name}' already exists.")

        await self._repository.add_category(category)
        return category

    async def update_category(
        self,
        category_id: int,
        name: str,
        description: str | None = None,
    ) -> Category | None:
        """Update an existing category's name and description.

        Returns the updated Category or None if the category does not exist.
        """
        category = await self._repository.get_by_id(category_id)
        if category is None:
            return None

        # Check for duplicate name if the name is changing
        cleaned_name = name.strip() if isinstance(name, str) else name
        if category.name != cleaned_name:
            existing = await self._repository.get_by_name(cleaned_name)
            if existing is not None and existing.id != category_id:
                raise ValueError(f"Category with name '{cleaned_name}' already exists.")

        # Update domain entity (triggers validation on setters)
        category.name = name
        category.description = description

        await self._repository.update_category(category)
        return category

    async def get_category_by_id(self, category_id: int) -> Category | None:
        """Retrieve a category by its ID."""
        return await self._repository.get_by_id(category_id)

    async def list_categories(self) -> list[Category]:
        """Retrieve all categories."""
        return await self._repository.list_all()

    # Convenient aliases
    get_by_id = get_category_by_id
    list_all = list_categories
