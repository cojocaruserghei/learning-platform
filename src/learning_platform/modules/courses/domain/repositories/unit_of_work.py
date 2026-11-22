from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from learning_platform.modules.courses.domain.repositories.category_repository import (
    ICategoryRepository,
)


class IUnitOfWork(ABC):
    @property
    @abstractmethod
    def categories(self) -> ICategoryRepository:
        raise NotImplementedError

    @abstractmethod
    async def __aenter__(self) -> Self:
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError