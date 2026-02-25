import logging
from typing import Annotated, AsyncGenerator, Generator
from contextlib import contextmanager, asynccontextmanager

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from redis.asyncio import Redis
from redis import Redis as RedisSync
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff

from app import crud, models, schemas, enums
from app.config import settings
from app.utils import security
from app.utils.cache import Cache, RedisCache, redis_prefix
from app.utils.datetime import utcnow

logger = logging.getLogger(__name__)

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_STR}/login/access-token/",
)
reusable_oauth2_open = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_STR}/login/access-token/",
    auto_error=False
)

optional_reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_STR}/login/access-token/", auto_error=False
)


async def update_visit_date(db: AsyncSession, user: models.User):
    user.last_visited = utcnow().replace(tzinfo=None)
    db.add(user)
    await db.commit()
    await db.refresh(user)


engine_async = create_async_engine(
    settings.SQLALCHEMY_ASYNC_DATABASE_URI,
    pool_pre_ping=True,
    pool_size=50,
    max_overflow=50,
    echo=False,  #! echo
)

async_session = sessionmaker(
    bind=engine_async,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator:
    async with async_session() as session:
        yield session


DbDependency = Annotated[AsyncSession, Depends(get_db)]


engine_sync = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_size=50,
    max_overflow=50,
    echo=False,
)

SessionFactory = sessionmaker(
    bind=engine_sync,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

@contextmanager
def get_db_sync() -> Generator[Session, None, None]:
    "Only for celery"
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


DbSyncDependency = Annotated[Session, Depends(get_db_sync)]


redis_client = Redis.from_url(
settings.REDIS_URL,
    socket_timeout=10,          # Таймаут одной операции
    socket_connect_timeout=5,   # Таймаут подключения
    retry=Retry(ExponentialBackoff(), 3),  # Автоповтор при ошибках
    health_check_interval=30,   # Проверка здоровья соединения
)

redis_sync = RedisSync.from_url(
settings.REDIS_URL,
    socket_timeout=10,          # Таймаут одной операции
    socket_connect_timeout=5,   # Таймаут подключения
)


async def get_redis() -> AsyncGenerator[Redis, None]:
    async def test_redis(connection: Redis) -> bool:
        try:
            await connection.ping()
            return True
        except Exception as e:
            logging.error(f"Redis connection test failed: {str(e)}")
            return False

    if await test_redis(redis_client):
        # try:
        yield redis_client
        # finally:
        #     await redis_client.close()
    else:
        await redis_client.close()
        raise HTTPException(status_code=503, detail="Redis unavailable")


RedisDependency = Annotated[Redis, Depends(get_redis)]

def get_redis_sync() -> RedisSync | None:
    def test_redis(connection: RedisSync) -> bool:
        try:
            connection.ping()
            return True
        except Exception as e:
            logging.error(f"Redis connection test failed: {str(e)}")
            return False

    if test_redis(redis_sync):
        try:
            return redis_sync
        finally:
            redis_sync.close()
    else:
        redis_sync.close()
        raise RuntimeError("Redis unavailable")


RedisSyncDependency = Annotated[RedisSync, Depends(get_redis_sync)]


async def get_redis_cache(
    redis: RedisDependency,
) -> RedisCache | None:
    if redis is not None:
        return RedisCache(redis)


RedisCacheDependency = Annotated[RedisCache, Depends(get_redis_cache)]


async def get_cache(redis: RedisDependency):
    return Cache(redis=redis, ttl=settings.CACHE_TTL)


CacheDependency = Annotated[Cache, Depends(get_cache)]


async def get_cache_wo_depends():
    return Cache(redis=redis_client, ttl=settings.CACHE_TTL)


async def get_current_user_or_none(
    db: DbDependency,
    redis_cache: RedisCacheDependency,
    token: Annotated[str | None, Depends(optional_reusable_oauth2)] = None,
) -> models.User | None:
    """

    Функция нужна для ендпоинтов на которых отображается добавлено ли объявление в избранное.
    Если пользователь залогинен - мы ему отображаем добавлен ли объект в избранное или нет, иначе возвращаем False

    """

    if not token:
        return None

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)

    except (jwt.JWTError, ValidationError) as e:
        logger.error(f"jwt.JWTError: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось проверить доступ",
        )
    user_id = token_data.sub
    user = await redis_cache.try_cache_object_pickle(
        name=redis_prefix.user.format(user_id),
        func=crud.user.get,
        db=db,
        id=user_id,
    )
    if not user:
        return None
    user.jwt_payload = payload
    await update_visit_date(db=db, user=user)
    return user


async def get_current_active_user_or_none(
    current_user: models.User | None = Depends(get_current_user_or_none),
) -> models.User | None:
    if current_user and not current_user.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован или удален")
    return current_user


CurrentActiveUserOrNoneDependency = Annotated[models.User | None, Depends(get_current_active_user_or_none)]


async def get_current_user(
    db: DbDependency,
    redis_cache: RedisCacheDependency,
    token: Annotated[str, Depends(reusable_oauth2)],
) -> models.User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось проверить доступ",
        )
    user_id = token_data.sub
    user = await redis_cache.try_cache_object_pickle(
        name=redis_prefix.user.format(user_id),
        func=crud.user.get,
        db=db,
        id=user_id,
    )
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    user.jwt_payload = payload
    await update_visit_date(db=db, user=user)
    return user


async def get_current_user_for_open_api(
    db: DbDependency,
    redis_cache: RedisCacheDependency,
    token: Annotated[str | None, Depends(reusable_oauth2_open)],
) -> models.User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось проверить доступ",
        )
    user_id = token_data.sub
    if redis_cache:
        redis_name = redis_prefix.user.format(user_id)
        user = await crud.user.get_try_cache(
            db, redis_cache=redis_cache, redis_name=redis_name, id=user_id
        )
    else:
        user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    user.jwt_payload = payload
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован или удален")
    await update_visit_date(db=db, user=user)
    return user

CurrentActiveUserDependencyForOpenApi = Annotated[models.User | None, Depends(get_current_user_for_open_api)]


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован или удален")
    return current_user


CurrentActiveUserDependency = Annotated[models.User, Depends(get_current_active_user)]


async def get_current_su(
    current_user: models.User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return current_user


async def get_current_active_su(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return current_user


CurrentActiveSuperUserDependency = Annotated[
    models.User, Depends(get_current_active_su)
]




