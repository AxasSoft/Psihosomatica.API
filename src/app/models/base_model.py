from typing import Any

from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:

        return cls.__name__.lower()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}[id={self.id}]"

    def __repr__(self) -> str:
        return str(self)

    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
