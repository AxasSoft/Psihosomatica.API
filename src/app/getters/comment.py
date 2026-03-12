from typing import Optional

from app.getters import get_user_short_info
from app.getters.timestamp import to_timestamp
from app.models import Comment, User
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import GettingComment


async def get_comment(db: AsyncSession, db_obj: Comment, db_user: Optional[User]):
    return GettingComment(
        id=db_obj.id,
        text=db_obj.text,
        created=to_timestamp(db_obj.created),
        user=await get_user_short_info(db_obj=db_obj.user)
    )
