from datetime import datetime, date
from typing import Type, TypeVar

from pydantic import BaseModel

from app.models.base_model import Base
from app.utils.datetime import to_unix_timestamp

SchemaType = TypeVar("SchemaType", bound=BaseModel)


def transform(db_obj: Base, target_schema: Type[SchemaType], **kwargs) -> SchemaType:
    data = {}
    for key in db_obj.__table__.columns.keys():
        if key in target_schema.model_fields:
            attr = getattr(db_obj, key)
            if isinstance(attr, datetime) or isinstance(attr, date):
                attr = to_unix_timestamp(attr)
            data[key] = attr
    data.update(kwargs)
    return target_schema(**data)
