from learning_platform.modules.courses.domain.entities.category import Category
from learning_platform.modules.courses.domain.repositories.category_repository import (
    ICategoryRepository,
)


class CategoryService:


    def __init__(self, repository: ICategoryRepository) -> None:
        self._repository = repository

    async def create_category(
        self, name: str, description: str | None = None
    ) -> Category:

        category = Category(name=name, description=description)

        existing = await self._repository.get_by_name(category.name)
        if existing is not None:
            raise ValueError(f"Category with name '{category.name}' already exists.")

        await self._repository.add_category(category)
        return category

    async def get_category_by_id(self, category_id: int) -> Category | None:
        return await self._repository.get_by_id(category_id)

    async def list_categories(self) -> list[Category]:
        return await self._repository.list_all()

    # Convenient aliases
    get_by_id = get_category_by_id
    list_all = list_categories
