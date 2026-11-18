from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learning_platform.modules.courses.domain.entities.category import Category
from learning_platform.modules.courses.domain.repositories.category_repository import (
    ICategoryRepository,
)
from learning_platform.modules.courses.infrastructure.persistence.models.category_model import (
    CategoryModel,
)


class SqlAlchemyCategoryRepository(ICategoryRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: CategoryModel) -> Category:
        return Category(
            id=model.id,
            name=model.name,
            description=model.description,
        )

    @staticmethod
    def _to_model(entity: Category) -> CategoryModel:
        if entity.id is not None:
            return CategoryModel(
                id=entity.id,
                name=entity.name,
                description=entity.description,
            )
        return CategoryModel(
            name=entity.name,
            description=entity.description,
        )

    async def add_category(self, category: Category) -> None:
        if category.id is not None:
            model = await self._session.get(CategoryModel, category.id)
            if model is not None:
                model.name = category.name
                model.description = category.description
                return

        model = self._to_model(category)
        self._session.add(model)
        await self._session.flush()
        if model.id is not None:
            category.id = model.id

    async def delete(self, category: Category) -> None:
        if category.id is None:
            return

        model = await self._session.get(CategoryModel, category.id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()

    async def get_by_id(self, category_id: int) -> Category | None:
        model = await self._session.get(CategoryModel, category_id)
        if model is None:
            return None
        return self._to_entity(model)

    async def get_by_name(self, name: str) -> Category | None:
        stmt = select(CategoryModel).where(CategoryModel.name == name)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def list_all(self) -> list[Category]:
        stmt = select(CategoryModel).order_by(CategoryModel.id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
