from abc import ABC, abstractmethod
from typing import List

from learning_platform.modules.courses.domain.entities.category import Category


class ICategoryRepository(ABC):
    @abstractmethod
    async def add_category(self, category) -> None:
        pass
    @abstractmethod
    async def delete(self, category) -> None:
        pass
    @abstractmethod
    async def get_by_id(self, category_id:int) ->Category | None:
        pass
    @abstractmethod
    async def get_by_name(self, name:str) ->Category | None:
        pass
    @abstractmethod
    async def list_all(self) -> List[Category]:
        pass