import logging

from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models import Hashtag, Story, StoryAttachment, StoryHashtag
from ..schemas import GettingHashtag
from sqlalchemy.ext.asyncio import AsyncSession

async def get_hashtag(db: AsyncSession, db_obj: Hashtag) -> GettingHashtag:
    await db.refresh(db_obj, ["hashtag_stories"])
    return GettingHashtag(
        id=db_obj.id,
        text=db_obj.text,
        stories_count=len(db_obj.hashtag_stories),
        cover=(
            await db.execute(
                select(StoryAttachment.main_link)
                .join(Story)
                .join(StoryHashtag)
                .where(StoryHashtag.hashtag_id == db_obj.id)
                .limit(1)
            )
        ).scalar_one_or_none()
    )
