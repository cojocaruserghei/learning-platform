class Category:
    def __init__(
        self,
        name: str,
        description: str | None = None,
        id: int | None = None,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description

    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, value: int | None) -> None:
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise TypeError("Category id must be an integer or None.")
        if value is not None and value <= 0:
            raise ValueError("Category id must be a positive integer.")
        self._id = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Category name must be a string.")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Category name cannot be empty or whitespace.")
        if len(cleaned) > 100:
            raise ValueError("Category name cannot exceed 100 characters.")
        self._name = cleaned

    @property
    def description(self) -> str | None:
        return self._description

    @description.setter
    def description(self, value: str | None) -> None:
        if value is not None:
            if not isinstance(value, str):
                raise TypeError("Category description must be a string or None.")
            if len(value) > 500:
                raise ValueError("Category description cannot exceed 500 characters.")
        self._description = value

    def __repr__(self) -> str:
        return (
            f"Category(id={self.id!r}, name={self.name!r}, "
            f"description={self.description!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Category):
            return NotImplemented
        # If both have IDs, compare by identity; otherwise compare by field values
        if self.id is not None and other.id is not None:
            return self.id == other.id
        return (
            self.id == other.id
            and self.name == other.name
            and self.description == other.description
        )
