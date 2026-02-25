from typing import Any, Type, TypeVar, Generic

from pydantic import BaseModel
from sqlalchemy import Select, delete, inspect, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.base_model import Base
from app.utils.pagination import get_page_async

ModelType = TypeVar("ModelType", bound=Base)
CreatingSchemaType = TypeVar("CreatingSchemaType", bound=BaseModel)
UpdatingSchemaType = TypeVar("UpdatingSchemaType", bound=BaseModel)

class AsyncCRUDBase(Generic[ModelType, CreatingSchemaType, UpdatingSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> ModelType | None:
        return await db.get(self.model, id)

    async def get_many(self, db: AsyncSession, ids: list[Any]) -> list[ModelType]:
        stmt = select(self.model).filter(self.model.id.in_(ids))
        res = await db.execute(stmt)
        return res.scalars().unique().all()

    async def get_all(self, db: AsyncSession) -> list[ModelType]:
        stmt = select(self.model)
        res = await db.execute(stmt)
        return res.scalars().unique().all()

    async def get_by(self, db: AsyncSession, **kwargs) -> ModelType | None:
        stmt = select(self.model).filter_by(**kwargs)
        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_many_by(self, db: AsyncSession, **kwargs) -> ModelType | None:
        stmt = select(self.model).filter_by(**kwargs)
        res = await db.execute(stmt)
        return res.scalars().all()

    def sync_get_many_by(self, db: Session, **kwargs) -> ModelType | None:
        "Метод нужен только для задач celery, возможно стоит вынести логику в отдельный класс"
        stmt = select(self.model).filter_by(**kwargs)
        res = db.execute(stmt)
        return res.scalars().all()

    def _get_columns_and_relationships(self) -> list[str]:
        "returns self.model columns and relationships"
        columns = [c.name for c in self.model.__mapper__.columns]  # OR__table__.columns
        relationships = [r.key for r in self.model.__mapper__.relationships]
        return columns + relationships

    def _filters(self, stmt: Select, filters: dict[str, Any]) -> Select:
        "adds simple filters"
        cols_rels = self._get_columns_and_relationships()
        conditions = []

        for name, value in filters.items():
            if name in cols_rels and value is not None:
                column_attr = getattr(self.model, name)
                if isinstance(value, (list, tuple, set)):
                    conditions.append(column_attr.in_(value))
                else:
                    conditions.append(column_attr == value)
        if conditions:
            stmt = stmt.where(*conditions)
        return stmt

    def _filter_between(
            self,
            stmt: Select,
            min_: int | None = None,
            max_: int | None = None,
            *,
            name_attr: str,
    ) -> Select:
        conditions = []
        column = getattr(self.model, name_attr, None)
        if column is None:
            raise AttributeError(f"Модель {self.model.__name__} не имеет атрибута '{name_attr}'")

        if min_ is not None:
            conditions.append(column >= int(min_))
        if max_ is not None:
            conditions.append(column <= int(max_))

        if conditions:
            stmt = stmt.where(and_(*conditions))
        return stmt

    def _orders(self, stmt: Select, order_by: str | None = None):
        cols_rels = self._get_columns_and_relationships()
        is_desc = True
        order_by = order_by.lower() if order_by else None

        if order_by and not order_by.startswith("-"):
            is_desc = False

        elif order_by and order_by.startswith("-"):
            order_by = order_by[1:]

        if order_by in cols_rels:
            collumn_attr = getattr(self.model, order_by)
            stmt = stmt.order_by(collumn_attr.desc()) if is_desc else stmt.order_by(collumn_attr)
        else:
            stmt = stmt.order_by(self.model.id.desc()) if is_desc else stmt.order_by(self.model.id)

        return stmt

    async def get_page(
            self,
            db: AsyncSession,
            order_by: Any = None,
            page: int | None = None,
            size: int = 30,
            **kwargs,
    ):
        stmt = select(self.model)
        if order_by is None:
            if hasattr(self.model, "created"):
                stmt = stmt.order_by(self.model.created.desc())
            elif hasattr(self.model, "id"):
                stmt = stmt.order_by(self.model.id)
        else:
            stmt = stmt.order_by(order_by)
        stmt = self._filters(stmt, kwargs)
        return await get_page_async(db, stmt, page, size)

    async def _adapt_fields(
            self, obj: dict[str, Any] | BaseModel, **kwargs
    ) -> dict[str, Any]:
        "pydantic model to dict+kwargs"
        data = (
            obj.model_dump(exclude_unset=True)
            if not isinstance(obj, dict)
            else obj
        )
        data.update(**kwargs)
        return data

    async def _set_db_obj_fields(self, db_obj: ModelType, fields: dict[str, Any]):
        "dict to sqlalchemy model"
        info = inspect(self.model)
        for field in info.columns.keys() + info.relationships.keys():
            if field in fields:
                setattr(db_obj, field, fields[field])
        return db_obj

    async def create(
            self, db: AsyncSession, *, obj_in: CreatingSchemaType | dict[str, Any], **kwargs
    ) -> ModelType:
        fields = await self._adapt_fields(obj_in, **kwargs)
        db_obj = await self._set_db_obj_fields(db_obj=self.model(), fields=fields)
        db.add(db_obj)
        await db.commit()
        return db_obj

    async def update(
            self,
            db: AsyncSession,
            *,
            db_obj: ModelType,
            obj_in: UpdatingSchemaType | dict[str, Any],
            **kwargs,
    ) -> ModelType:
        fields = await self._adapt_fields(obj_in, **kwargs)
        db_obj = await self._set_db_obj_fields(db_obj=db_obj, fields=fields)
        await db.commit()
        return db_obj

    async def remove_by_id(self, db: AsyncSession, *, id: Any) -> ModelType | None:
        await db.execute(delete(self.model).where(self.model.id == id))
        return None

    async def remove_obj(self, db: AsyncSession, *, obj: ModelType) -> ModelType | None:
        await db.delete(obj)
        return None

    async def remove_by_ids(
            self, db: AsyncSession, *, ids: list[Any]
    ) -> list[ModelType] | None:
        await db.execute(delete(self.model).where(self.model.id.in_(ids)))
        return None

    async def remove_many_obj(
            self, db: AsyncSession, *, objs: list[ModelType]
    ) -> list[ModelType] | None:
        await db.execute(
            delete(self.model).where(self.model.id.in_([obj.id for obj in objs]))
        )
        return None