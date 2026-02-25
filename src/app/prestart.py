import logging
import asyncio

from app.config import settings
from app.utils.security import get_password_hash
from sqlalchemy import text, Boolean as SA_Boolean
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

# Асинхронный движок
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI.replace("postgresql://", "postgresql+asyncpg://"),
    pool_pre_ping=True,
)

# Асинхронная сессия
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

logger = logging.getLogger(__name__)

max_tries = 60 * 2  # 2 минуты
wait_seconds = 2


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def init() -> None:
    """Создает суперпользователя, если он не создан"""
    async with AsyncSessionLocal() as session:
        stmt = text(
            f"""SELECT * FROM public.user WHERE "email"=:email"""
        )
        res = await session.execute(stmt, {"email": settings.FIRST_SUPERUSER})
        if not res.all():
            hashed_password = get_password_hash(settings.FIRST_SUPERUSER_PASSWORD)
            stmt = text(
                """INSERT INTO public.user 
                (email, hashed_password, is_superuser, first_name, last_name, patronymic, gender, is_active)
                VALUES (:email, :hashed_password, :is_superuser, :first_name, :last_name, :patronymic, :gender, :is_active)
                """
            )
            await session.execute(
                stmt,
                {
                    "email": settings.FIRST_SUPERUSER,
                    "hashed_password": hashed_password,
                    "is_superuser": True,
                    "first_name": "admin",
                    "last_name": "admin",
                    "patronymic": "admin",
                    "gender": "man",
                    "is_active": True,
                },
            )
            await session.commit()
            logger.info("Superuser added!")


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def wait_db() -> None:
    """Проверяет, готова ли база данных"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            logger.info("Database is ready!")
    except Exception as e:
        logger.error(e)
        raise e


async def main() -> None:
    logger.info("Initializing service")
    await wait_db()
    await init()
    logger.info("Service finished initializing")


if __name__ == "__main__":
    asyncio.run(main())
