from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from learning_platform.shared.infrastructure.persistence.base import OrmBase


class CategoryModel(OrmBase):
    __tablename__ = "categories"
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(500))