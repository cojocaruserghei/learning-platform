from abc import ABC, abstractmethod

from learning_platform.modules.courses.domain.repositories.category_repository import (
    ICategoryRepository,
)


class IUnitOfWork(ABC):
    @property
    @abstractmethod
    def categories(self) -> ICategoryRepository:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError