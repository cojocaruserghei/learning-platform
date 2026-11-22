from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from learning_platform.modules.courses.domain.repositories.category_repository import (
    ICategoryRepository,
)
from learning_platform.modules.courses.domain.repositories.unit_of_work import (
    IUnitOfWork,
)
from learning_platform.modules.courses.infrastructure.persistence.repositories.sqlalchemy_category_repository import (
    SqlAlchemyCategoryRepository,
)


class SqlAlchemyUnitOfWork(IUnitOfWork):

    def __init__(self, session: AsyncSession):
        self._session = session
        self._categories = SqlAlchemyCategoryRepository(self._session)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    @property
    def categories(self) -> ICategoryRepository:
        return self._categories

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()