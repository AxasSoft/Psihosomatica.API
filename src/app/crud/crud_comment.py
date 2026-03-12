from typing import Optional, Type

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.crud import AsyncCRUDBase
from app.models.story import Story
from app.models.user import User
from app.schemas.story import CreatingStory, UpdatingStory
from ..models import Comment, UserBlock
from ..schemas import CreatingComment
from ..utils import pagination
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDComment(AsyncCRUDBase[Story, CreatingStory, UpdatingStory]):

    def __init__(self, model: Type[Story]):
        super().__init__(model=model)

    async def comment_story(self, db: AsyncSession, *, user: User, story: Story, obj_in: CreatingComment):
        comment = Comment()
        comment.story = story
        comment.user = user
        comment.text = obj_in.text
        db.add(comment)
        db.add(user)
        await db.commit()
        await db.refresh(comment)

        return comment

    async def get_story_comments(self, db: AsyncSession, story: Story, page: Optional[int], current_user: Optional[User] = None):
        return await pagination.get_page_async(
            db,
            (
                story.comments
                    .join(UserBlock, Comment.user_id == UserBlock.object_id, isouter=True)
                    .filter(UserBlock.id == None)
                    .order_by(desc(Comment.created))
            ),
            page
        )


comment = CRUDComment(Comment)
