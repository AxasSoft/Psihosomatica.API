from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.getters.universal import transform
from app.models import User
from app.schemas import GettingUser, GettingUserShortInfo

async def get_user(db: AsyncSession, user: User) -> GettingUser:
    return transform(
        user,
        GettingUser,
    )


async def get_user_short_info(db: AsyncSession, user: User) -> GettingUserShortInfo:
    return transform(
        user,
        GettingUserShortInfo,
    )


