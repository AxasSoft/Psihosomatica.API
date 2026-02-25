from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.getters.universal import transform
from app.models import User
from app.schemas import GettingUser

async def get_user(db: AsyncSession, user: User) -> GettingUser:
    return transform(
        user,
        GettingUser,
    )


