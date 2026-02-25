import json
import logging
import pickle
from typing import Any, Coroutine, Type
from datetime import datetime, date

from pydantic import BaseModel
from app.utils.datetime import to_unix_timestamp

from app.models.base_model import Base
from redis.asyncio import Redis


class RedisPrefix:
    pass

redis_prefix = RedisPrefix()


class RedisCache:
    """Класс содержит методы для кеширования объектов в Redis.

    :try_cache_object_json: кеширует объект SQLAlchemy в json.
    при восстановлении из кеша объект теряет метаданные и связь с БД
    :try_cache_dict: кеширует dict объект
    :try_cache_object_pickle: кеширует SQLAlchemy объект используя pickle. объект не теряет метаданные.
    для использования из кеша в контексте сессии его нужно добавить в сессию session.add(object)
    :try_cache_object_list_pickle: то же что и try_cache_object_pickle, только для списка объектов
    """

    def __init__(self, redis: Redis):
        self.redis = redis

    @staticmethod
    def _serialize_object(obj):
        """Serialize SQLAlchemy object to JSON."""
        data = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            if hasattr(value, "value"):
                value = value.value
            elif isinstance(value, (datetime, date)):
                value = to_unix_timestamp(value)
            data[column.name] = value
        return json.dumps(data)

    @staticmethod
    def _deserialize_object(data, model):
        """Deserialize JSON back to SQLAlchemy object."""
        obj_data = json.loads(data)
        return model(**obj_data)

    async def try_cache_object_json(
        self, model: Base, name: str, func: Coroutine, ex: int | None = 30, **kwargs
    ) -> dict:
        """кэширует SQLAlchemy object в JSON формате. пробует найти в кэше. при неудаче использует функцию c kwargs.

        теряет метаданные объекта, то есть объект создается заново при восстановлении из кеша и не связан с БД"""
        object_json = await self.redis.get(name)
        if object_json:
            msg = "from_cache"
            object_db = self._deserialize_object(object_json, model)
        else:
            msg = "from_db"
            object_db = await func(**kwargs)
            if object_db:
                object_json = self._serialize_object(object_db)
                await self.redis.set(name, object_json, ex=ex)
        logging.info("%s %s:\n\t%s", name, msg, object_db)
        return object_db

    async def try_cache_dict(
        self, name: str, func: Coroutine, ex: int | None = 30, **kwargs
    ) -> dict:
        "кэширует dict. пробует найти в кэше. при неудаче использует функцию c kwargs"
        result = await self.redis.get(name)
        if result:
            msg = "from_cache"
            result = json.loads(result)
        else:
            msg = "from_db"
            result = await func(**kwargs)
            await self.redis.set(name, json.dumps(result), ex=ex)
        logging.info("%s %s:\n\t%s", name, msg, result)
        return result

    async def try_cache_object_pickle(
        self, name: str, func: Coroutine, ex: int | None = 30, **kwargs
    ):
        "кэширует SQLAlchemy object. пробует найти в кэше. при неудаче использует функцию c kwargs"
        object_pickle = await self.redis.get(name)
        if object_pickle:
            msg = "from_cache"
            object = pickle.loads(object_pickle)
        else:
            msg = "from_db"
            object = await func(**kwargs)
            if object:
                object_pickle = pickle.dumps(object)
                await self.redis.set(name, object_pickle, ex=ex)
        logging.info("%s %s:\n\t%s", name, msg, object)
        return object

    async def try_cache_object_list_pickle(
        self, name: str, func: Coroutine, ex: int | None = 30, **kwargs
    ) -> list:
        "кэширует SQLAlchemy objects list. пробует найти в кэше. при неудаче использует функцию c kwargs"
        ls_pickle = await self.redis.lrange(name, 0, -1)
        if ls_pickle:
            msg = "from_cache"
            db_ls = [pickle.loads(object_pickle) for object_pickle in ls_pickle]
        else:
            msg = "from_db"
            db_ls = await func(**kwargs)
            if db_ls:
                ls_pickle = [pickle.dumps(object_db) for object_db in db_ls]
                await self.redis.lpush(name, *ls_pickle)
                await self.redis.expire(name, ex)
        logging.info("%s %s:\n\t%s", name, msg, db_ls)
        return db_ls

    async def try_cache_paginated_data(
            self,
            name: str,
            func: Coroutine,
            ex: int | None = 30,
            **kwargs
    ) -> tuple[list, Any]:
        """Кэширует данные с пагинацией.
        Возвращает кортеж (данные, пагинатор)"""
        cached_data = await self.redis.get(name)
        if cached_data:
            msg = "from_cache"
            data, paginator = pickle.loads(cached_data)
        else:
            msg = "from_db"
            data, paginator = await func(**kwargs)
            if data:
                await self.redis.set(name, pickle.dumps((data, paginator)), ex=ex)
        logging.info("%s %s", name, msg)
        return data, paginator


class Cache:
    def __init__(self, redis: Redis, ttl):
        self.redis = redis
        self.ttl = ttl

    @staticmethod
    def format_key(key_tuple: tuple) -> bytes:
        return (":".join(str(item) for item in key_tuple)).encode()

    @staticmethod
    def encode_body(body: BaseModel):
        return json.dumps(body).encode()

    @staticmethod
    def decode_body(body: bytes):
        return json.loads(body.decode())

    async def get_raw(self, key_tuple: tuple):
        key = self.format_key(key_tuple)
        data = await self.redis.get(key)
        if data is None:
            return None

        return self.decode_body(data)

    async def set_raw(self, key_tuple: tuple, body: Any, ttl=None):
        key = self.format_key(key_tuple)
        data = self.encode_body(body)
        await self.redis.set(key, data, ex=self.ttl if ttl is None else ttl)

    async def get(self, key_tuple: tuple):
        data = await self.get_raw(key_tuple)
        if data is None:
            return None

        return data

    async def set(self, key_tuple: tuple, body: BaseModel | dict, ttl=None):
        if body is not None and isinstance(body, BaseModel):
            body = body.model_dump()
        await self.set_raw(key_tuple, body if body is not None else None, ttl)

    async def delete(self, key_tuple: tuple):
        key = self.format_key(key_tuple)
        await self.redis.delete(key)

    async def delete_by_prefix(self, prefix: str):
        for key in await self.redis.keys(prefix + "*"):
            await self.redis.delete(key)

    async def behind_cache(self, key_tuple, func, ttl=None, **kwargs):
        "data.data: from db -> PydanticModel, from cache -> dict"

        data = await self.get(key_tuple)
        if data is not None:
            logging.info("from cache =>")
            return data, True

        logging.info("from db =>")
        data = await func(**kwargs)
        await self.set(key_tuple, data, ttl)
        return data, False

    async def get_keys(self, prefix: str):
        return await self.redis.keys(prefix)

    async def behind_cache_raw(self, key_tuple, func, ttl=None):
        data = await self.get_raw(key_tuple)
        if data is not None:
            return data, True

        data = await func()
        await self.set(key_tuple, data, ttl)
        return data, False

    async def incr(self, key_tuple: tuple) -> int:
        key = self.format_key(key_tuple)
        return await self.redis.incr(key)
