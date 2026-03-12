import logging
import datetime
from typing import Optional, List

from app.models import User
from sqlalchemy import not_, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from .hashtag import get_hashtag
from .users import get_user_short_info
from .story_attachment import get_story_attachment
from .timestamp import to_timestamp
from ..enums.reaction import ReactionType
from ..models import Story, StoryAttachment, Reaction
from ..models.view import View
from ..models.hug import Hug
from ..schemas import GettingStory, GettingUserStories
from sqlalchemy import select


async def get_story(db: AsyncSession, db_obj: Story, db_user: Optional[User] = None) -> GettingStory:
    videos = [att for att in db_obj.attachments if not att.is_image]
    video = videos[0] if len(videos) > 0 else  None
    images = [att for att in sorted(db_obj.attachments, key=lambda x: x.id) if att.is_image]
    is_comment = any(comment.user == db_user for comment in db_obj.comments) if db_user is not None else None
    result = await db.execute(
        select(
            Reaction.type_reaction,
            func.count(Reaction.id).label("total_count"),
            func.count(Reaction.id)
            .filter(Reaction.user_id == db_user.id)
            .label("user_count"),
        )
        .where(Reaction.story_id == db_obj.id)
        .group_by(Reaction.type_reaction)
    )
    rows_for_reaction = result.all()
    reactions_count = {}
    reacted = {}
    for reaction_type, total_count, user_count in rows_for_reaction:
        reactions_count[reaction_type.value] = total_count
        reacted[reaction_type.value] = user_count > 0
    for rt in ReactionType:
        reactions_count.setdefault(rt.value, 0)
        reacted.setdefault(rt.value, False)

    result = GettingStory(
        id=db_obj.id,
        created=to_timestamp(db_obj.created),
        user=await get_user_short_info(db, db_obj.user),
        text=db_obj.text,
        title=db_obj.title,
        video=await get_story_attachment(video) if video is not None else None,
        gallery=[await get_story_attachment(item) for item in images],
        is_private=db_obj.is_private,
        is_short_story=db_obj.is_short_story,
        hashtags=[
            await get_hashtag(db, story_hashtag.hashtag) for story_hashtag in db_obj.story_hashtags
        ],
        views_count=len(db_obj.views),
        viewed=len([view for view in db_obj.views if view.user == db_user]) > 0 if db_user is not None else None,
        hugs_count=len(db_obj.hugs),
        hugged=len([hug for hug in db_obj.hugs if hug.user == db_user]) > 0 if db_user is not None else None,
        reactions_count = reactions_count,
        reacted = reacted,
        comments_count=len(db_obj.comments),
        is_favorite=len([fav for fav in db_obj.favorite_stories if fav.user == db_user]) > 0 if db_user is not None else None,
        is_comment=is_comment
    )


    return result

async def get_grouped_short_story(db: AsyncSession, stories: List[Story], db_user: User):
    stories_list = [
        GettingStory(
            **(await get_story(db=db, db_obj=story).dict())
        )
        for story in stories
    ]
    return GettingUserStories(
        user=await get_user_short_info(stories[0].user),
        stories=stories_list
    )
