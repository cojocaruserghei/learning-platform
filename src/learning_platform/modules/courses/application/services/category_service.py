from learning_platform.modules.courses.domain.entities.category import Category
from learning_platform.modules.courses.domain.repositories.unit_of_work import (
    IUnitOfWork,
)


class CategoryService:

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def create_category(
        self, name: str, description: str | None = None
    ) -> Category:

        category = Category(name=name, description=description)

        existing = await self._uow.categories.get_by_name(category.name)
        if existing is not None:
            raise ValueError(f"Category with name '{category.name}' already exists.")

        try:
            await self._uow.categories.add_category(category)
            await self._uow.commit()
        except Exception:
            await self._uow.rollback()
            raise
        return category

    async def update_category(
        self,
        category_id: int,
        name: str,
        description: str | None = None,
    ) -> Category | None:

        category = await self._uow.categories.get_by_id(category_id)
        if category is None:
            return None

        # Check for duplicate name if the name is changing
        cleaned_name = name.strip() if isinstance(name, str) else name
        if category.name != cleaned_name:
            existing = await self._uow.categories.get_by_name(cleaned_name)
            if existing is not None and existing.id != category_id:
                raise ValueError(f"Category with name '{cleaned_name}' already exists.")

        # Update domain entity (triggers validation on setters)
        category.name = name
        category.description = description
        try:
            await self._uow.categories.update_category(category)
            await self._uow.commit()
        except Exception:
            await self._uow.rollback()
            raise
        return category

    async def get_category_by_id(self, category_id: int) -> Category | None:
        return await self._uow.categories.get_by_id(category_id)

    async def list_categories(self) -> list[Category]:
        return await self._uow.categories.list_all()

    # Convenient aliases
    get_by_id = get_category_by_id
    list_all = list_categories
