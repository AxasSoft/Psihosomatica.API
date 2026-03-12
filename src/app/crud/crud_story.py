import datetime
from typing import Any, Dict, Optional, Union, Type, List, Tuple

from sqlalchemy import or_, not_, and_, desc
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud import AsyncCRUDBase
from app.crud.crud_story_attachment import story_attachment as attachment_crud
from app.models import Hug, Device, FirebaseToken, FavoriteStory, Subscription
from app.models.story import Story
from app.models.user import User
from app.schemas.response import Paginator
from app.schemas.story import CreatingStory, UpdatingStory
from app.utils import pagination
from ..models import Hashtag, StoryHashtag, StoryAttachment, View, StoryHiding, UserBlock, Reaction
from app.enums.reaction import ReactionType


class CRUDStory(AsyncCRUDBase[Story, CreatingStory, UpdatingStory]):

    def __init__(self, model: Type[Story]):
        super().__init__(model=model)

    async def create_story_by_user(self, db: AsyncSession, *, user: User, obj_in: CreatingStory):
        db_obj = Story()
        db_obj.user = user
        db_obj.text = obj_in.text
        db_obj.is_private = obj_in.is_private if obj_in.is_private is not None else None
        db_obj.is_short_story = obj_in.is_short_story
        db.add(db_obj)

        db.add(user)

        attachments = []

        if obj_in.gallery is not None:
            not_found = []
            forbidden = []
            rebinding = []
            for index, attachment_id in enumerate(obj_in.gallery):
                attachment = await attachment_crud.get(db,id=attachment_id)
                if attachment is None:
                    not_found.append(index)
                    continue
                if attachment.story is not None:
                    rebinding.append(index)
                    continue
                attachments.append(attachment)
            if len(not_found) > 0:
                return None, -2, not_found
            if len(forbidden) > 0:
                return None, -3, forbidden
            if len(rebinding) > 0:
                return None, -4, rebinding

        if obj_in.video is not None:
            attachment = await attachment_crud.get(db,id=obj_in.video)
            if attachment is None:
                return None, -5, None
            if attachment.user != user:
                return None, -6, None
            if attachment.story is not None:
                return None, -7, None
            attachments.append(attachment)

        for attachment in attachments:
            attachment.story = db_obj
            db.add(attachment)

        for hashtag_text in obj_in.hashtags:
            hashtag_query = select(Hashtag).where(Hashtag.text == hashtag_text)
            hashtag = await db.execute(hashtag_query)
            hashtag = hashtag.scalar_one_or_none()
            if hashtag is None:
                hashtag = Hashtag()
                hashtag.text = hashtag_text
                db.add(hashtag)
            story_hashtag = StoryHashtag()
            story_hashtag.story = db_obj
            story_hashtag.hashtag = hashtag
            db.add(story_hashtag)

        await db.commit()
        await db.refresh(db_obj)

        return db_obj, 0, None


    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Story,
        obj_in:  Union[UpdatingStory, Dict[str, Any]]
    ):
        new_attachments = []
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        if 'text' in update_data:
            db_obj.text = obj_in.text
        if 'title' in update_data:
            db_obj.title = obj_in.title
        if 'is_private' in update_data:
            db_obj.is_private = obj_in.is_private if obj_in.is_private is not None else None
        db.add(db_obj)
        if 'gallery' in update_data:
            new_ids_in_gallery = update_data['gallery'] or []
            old_objs_in_gallery = db_obj.attachments.filter(StoryAttachment.is_image).all()
            old_ids_in_gallery = [item.id for item in old_objs_in_gallery]

            for_removing = []
            not_found = []
            forbidden = []
            rebinding = []

            for index, id_ in enumerate(old_ids_in_gallery):
                if id_ not in new_ids_in_gallery:
                    old_attachment = old_objs_in_gallery[index]
                    for_removing.append(old_attachment)
            for index, id_ in enumerate(new_ids_in_gallery):
                if id_ not in old_ids_in_gallery:
                    new_attachment = await attachment_crud.get(db,id=id_)
                    if new_attachment is None:
                        not_found.append(index)
                    if new_attachment.story is not None:
                        rebinding.append(index)
                    new_attachment.story = db_obj
                    db.add(new_attachment)

            if len(not_found) > 0:
                return None, -2, not_found
            if len(forbidden) > 0:
                return None, -3, forbidden
            if len(rebinding) > 0:
                return None, -4, rebinding

            for attachment in for_removing:
                await db.delete(attachment)

        if 'video' in update_data:
            old_video = db_obj.attachments.filter(not_(StoryAttachment.is_image)).first()
            new_video_id = update_data['video']
            if old_video is not None and old_video.id != update_data['video']:
                old_video.story = None
            if new_video_id is not None:
                new_video = await attachment_crud.get(db,id=new_video_id)
                if new_video is None:
                    return None, -5, None
                if new_video.user != db_obj.user:
                    return None, -6, None
                if new_video.story is not None:
                    return None, -7, None
                new_attachments.append(new_video)

        if 'hashtags' in update_data:
            result = await db.execute(
                select(Hashtag.text, StoryHashtag.id)
                .join(StoryHashtag, StoryHashtag.hashtag_id == Hashtag.id)
                .where(StoryHashtag.story_id == db_obj.id)
            )

            old_hashtags = {
                hashtag_text: id_
                for hashtag_text, id_ in result.all()
            }
            new_hashtags = update_data['hashtags']

            for hashtag_text, story_hashtag in old_hashtags.items():
                if hashtag_text not in new_hashtags:
                    await db.delete(story_hashtag)
            for hashtag_text in new_hashtags:
                if hashtag_text not in old_hashtags:
                    result = await db.execute(select(Hashtag).where(Hashtag.text == hashtag_text))
                    hashtag = result.scalar_one_or_none()
                    if hashtag is None:
                        hashtag = Hashtag()
                        hashtag.text = hashtag_text
                        db.add(hashtag)
                    story_hashtag = StoryHashtag()
                    story_hashtag.story = db_obj
                    story_hashtag.hashtag = hashtag
                    db.add(story_hashtag)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj, 0, None

    async def get_stories_by_user(
        self,
        db: Session,
        *,
        user: User,
        current_user: Optional[User] = None,
        page: Optional[int] = None,
        is_hugged: Optional[bool] = None,
        is_favorite: Optional[bool] = None,
        is_short_story: bool = False,
    ) -> Tuple[List[Story], Paginator]:
        now = datetime.datetime.utcnow()
        query = select(Story).filter(Story.user == user).order_by(desc(Story.created))

        if is_short_story:
            query = query.filter(
                Story.is_short_story == True,
                Story.created >= now - datetime.timedelta(hours=24)
            )
        else:
            query = query.filter(Story.is_short_story == False)

        if current_user is not None:
            query = (
                query
                    .join(
                        StoryHiding,
                        and_(StoryHiding.story_id == Story.id, StoryHiding.user_id == current_user.id),
                        isouter=True
                    )
                    .join(
                        UserBlock,
                        or_(
                            and_(UserBlock.object_id == current_user.id, UserBlock.subject_id == Story.user_id),
                            and_(UserBlock.subject_id == current_user.id, UserBlock.object_id == Story.user_id)
                        ),
                        isouter=True
                    )
                    .filter(StoryHiding.id == None, UserBlock.id == None)
            )

        if current_user is not None and is_hugged is not None:
            query = query.join(Hug, and_(Hug.story_id == Story.id, Hug.user_id == current_user.id),isouter=True)
            if is_hugged:
                query = query.filter(Hug.id != None)
            else:
                query = query.filter(Hug.id == None)


        if current_user is not None and is_favorite is not None:
            query = query.join(FavoriteStory, and_(FavoriteStory.story_id == Story.id, FavoriteStory.user_id == current_user.id),isouter=True)
            if is_favorite:
                query = query.filter(FavoriteStory.id != None)
            else:
                query = query.filter(FavoriteStory.id == None)

        return await pagination.get_page_async(db, query, page)


    async def get_stories_from_subscriptions(
            self,
            db,
            *,
            search: Optional[str] = None,
            hashtag: Optional[Hashtag] = None,
            is_hugged: Optional[bool] = None,
            is_favorite: Optional[bool] = None,
            page: Optional[int] = None,
            is_short_story: bool = False,
            current_user: User = None,
            host: Optional[str] = None,
            x_real_ip: Optional[str] = None,
            accept_language: Optional[str] = None,
            user_agent: Optional[str] = None,
            x_firebase_token: Optional[str] = None,
    ) -> Tuple[List[Story], Paginator]:

        query = select(Story)
        now = datetime.datetime.utcnow()

        if search is not None:
            query = query\
                .join(StoryHashtag, isouter=True)\
                .join(Hashtag, isouter=True)\
                .filter(
                    or_(
                        Hashtag.text.ilike(f'%{search}%'),
                        Story.text.ilike(f'%{search}%')
                    )
                )

        result = await db.execute(
            select(Subscription.object_id).where(Subscription.subject_id == current_user.id)
        )
        following_user_ids = [row[0] for row in result.all()]
        query = query.filter(Story.user_id.in_(following_user_ids))

        if is_short_story:
            query = query.filter(
                Story.is_short_story == True,
                Story.created >= now - datetime.timedelta(hours=24)
            )
        else:
            query = query.filter(Story.is_short_story == False)

        if hashtag is not None:
            query = query.join(StoryHashtag).filter(StoryHashtag.hashtag == hashtag)

        if current_user is not None and is_hugged is not None:
            query = query.join(Hug, and_(Hug.story_id == Story.id, Hug.user_id == current_user.id), isouter=True)
            if is_hugged:
                query = query.filter(Hug.id != None)
            else:
                query = query.filter(Hug.id == None)

        if current_user is not None and is_favorite is not None:
            query = query.join(FavoriteStory, and_(FavoriteStory.story_id == Story.id, FavoriteStory.user_id == current_user.id),isouter=True)
            if is_favorite:
                query = query.filter(FavoriteStory.id != None)
            else:
                query = query.filter(FavoriteStory.id == None)

        # query = query.filter(
        #     now - Story.created <= datetime.timedelta(days=90),
        # )

        query = query.order_by(desc(Story.created)).distinct()


        return await pagination.get_page_async(db, query, page)

    async def mark_story_as_viewed(
            self,
            db: AsyncSession,
            *,
            story: Story,
            user: User
    ):
        result = await db.execute(
            select(View).where(View.story == story, View.user == user)
        )
        view = result.scalar_one_or_none()
        if view is None:
            view = View()
            view.user = user
            view.story = story
            db.add(view)
            await db.commit()

    async def hug_story(
            self,
              db: AsyncSession,
              *,
              story: Story,
              user: User,
              hugs: bool
    ):
        result = await db.execute(
            select(Hug).where(Hug.story == story, Hug.user == user)
        )
        hug = result.scalar_one_or_none()

        if hug is None and hugs:
            hug = Hug()
            hug.story = story
            hug.user = user
            db.add(hug)
            await db.commit()


            await db.delete(hug)
            await db.commit()

    async def react_story(
            self,
            db: AsyncSession,
            *,
            story: Story,
            user: User,
            set_reaction: bool,
            type_reaction: ReactionType,
    ):
        result = await db.execute(
            select(Reaction).where(
                Reaction.story == story,
                Reaction.user == user,
                Reaction.type_reaction == type_reaction
            )
        )
        reaction = result.scalar_one_or_none()
        owner_story = story.user

        if reaction is None and set_reaction:
            reaction = Reaction()
            reaction.story = story
            reaction.user = user
            reaction.type_reaction = type_reaction
            db.add(reaction)

            await db.commit()

        if reaction is not None and not set_reaction:

            await db.delete(reaction)
            await db.commit()

    async def favorite_story(
                self,
                db: AsyncSession,
                *,
                story: Story,
                user: User,
                is_favorite: bool
    ):
        result = await db.execute(
            select(FavoriteStory).where(FavoriteStory.story_id == story.id, FavoriteStory.user == user)
        )
        fav = result.scalar_one_or_none()
        if fav is None and is_favorite:
            fav = FavoriteStory()
            fav.story = story
            fav.user = user
            db.add(fav)
            await db.commit()

        elif fav is not None and not is_favorite:
            await db.delete(fav)
            await db.commit()

    async def hide_story(
            self,
            db,
            *,
            story: Story,
            user: User,
            hide: bool
    ):
        result = await db.execute(
            select(StoryHiding).where(StoryHiding.story == story, StoryHiding.user == user)
        )
        hiding = result.scalar_one_or_none()
        if hiding is None and hide:
            hiding = StoryHiding()
            hiding.story = story
            hiding.user = user
            db.add(hiding)
            await db.commit()

        elif hiding is not None and not hide:
            await db.delete(hiding)
            await db.commit()

    async def get_stories(
            self,
            db,
            *,
            search: Optional[str],
            hashtag: Optional[Hashtag],
            user: Optional[User],
            is_hugged: Optional[bool] = None,
            is_favorite: Optional[bool] = None,
            is_short_story: bool = False,
            page: Optional[int] = None,
            current_user: Optional[User] = None,
    ) -> Tuple[List[Story], Paginator]:

        query = select(Story)
        now = datetime.datetime.utcnow()

        if is_short_story:
            query = query.filter(
                Story.is_short_story == True,
                Story.created >= now - datetime.timedelta(hours=24)
            )
        else:
            query = query.filter(Story.is_short_story == False)

        if search is not None:
            query = query \
                .join(StoryHashtag, isouter=True) \
                .join(Hashtag, isouter=True) \
                .filter(
                or_(
                    Hashtag.text.ilike(f'%{search}%'),
                    Story.text.ilike(f'%{search}%')
                )
            )

        if user is not None:
            query = query.filter(Story.user == user)
        if hashtag is not None:
            query = query.join(StoryHashtag).filter(StoryHashtag.hashtag == hashtag)

        if current_user is not None and is_hugged is not None:
            query = query.join(Hug, and_(Hug.story_id == Story.id, Hug.user_id == current_user.id), isouter=True)
            if is_hugged:
                query = query.filter(Hug.id != None)
            else:
                query = query.filter(Hug.id == None)

        if current_user is not None and is_favorite is not None:
            query = query.join(FavoriteStory, and_(FavoriteStory.story_id == Story.id, FavoriteStory.user_id == current_user.id),isouter=True)
            if is_favorite:
                query = query.filter(FavoriteStory.id != None)
            else:
                query = query.filter(FavoriteStory.id == None)


        # query = query.filter(
        #     now - Story.created <= datetime.timedelta(days=90),
        # )
        query = query.order_by(desc(Story.created)).distinct()

        return await pagination.get_page_async(db, query, page)

    async def get_short_stories_from_subscriptions(
            self,
            db,
            *,
            page: Optional[int] = None,
            current_user: User = None,
    ):

        result = await db.execute(
            select(Subscription.object_id).where(Subscription.subject_id == current_user.id)
        )
        following_user_ids = [row[0] for row in result.all()]

        result = await db.execute(
            select(Story.user_id)
            .where(
                Story.is_short_story.is_(True),
                Story.created >= datetime.datetime.utcnow() - datetime.timedelta(hours=24),
                Story.user_id.in_(following_user_ids)
            )
            .order_by(Story.user_id, Story.created.desc())
        )
        user_ids_with_stories = result.all()
        user_ids = [user_id for (user_id,) in user_ids_with_stories]

        if not user_ids:
            return [], None

        query = select(Story)
        now = datetime.datetime.utcnow()
        query = query.filter(
            Story.is_short_story.is_(True),
            Story.created >= now - datetime.timedelta(hours=24),
            Story.user_id.in_(following_user_ids)
        )
        result = await db.execute(query.order_by(Story.user_id, desc(Story.created)))
        all_stories = result.scalars().all()

        stories_by_user: Dict[int, List[Story]] = {}
        for story in all_stories:
            if story.user_id not in stories_by_user:
                stories_by_user[story.user_id] = []
            stories_by_user[story.user_id].append(story)

        grouped_stories = [
            stories_by_user[user_id]
            for user_id in user_ids
            if user_id in stories_by_user
        ]

        if page is not None:
            items_per_page = 30
            total_items = len(grouped_stories)
            total_pages = (total_items + items_per_page - 1) // items_per_page  # Округление вверх

            # Проверка на выход за границы
            if page < 1 or (page > total_pages and total_pages > 0):
                return [], None

            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            paginated_items = grouped_stories[start_idx:end_idx]

            paginator = Paginator(
                page=page,
                total=total_pages,
                total_count=total_items,
                has_prev=page > 1,
                has_next=page < total_pages
            )
            return paginated_items, paginator
        else:
            return grouped_stories, None

    async def get_short_stories(
            self,
            db,
            *,
            page: Optional[int] = None,
            current_user: Optional[User] = None,
    ) -> Tuple[List[Story], Paginator]:

        result = await db.execute(
            select(Story.user_id)
            .distinct()
            .where(
                Story.is_short_story.is_(True),
                Story.created >= datetime.datetime.utcnow() - datetime.timedelta(hours=24)
            )
            .order_by(Story.user_id, Story.created.desc())
        )
        user_ids_with_stories = result.all()
        user_ids =[user_id for (user_id,) in user_ids_with_stories]

        if not user_ids:
            return [], None

        query = select(Story)
        now = datetime.datetime.utcnow()
        query = query.filter(
            Story.is_short_story.is_(True),
            Story.created >= now - datetime.timedelta(hours=24)
        )
        result = await db.execute(query.order_by(Story.user_id, desc(Story.created)))
        all_stories = result.scalars().all()
        stories_by_user: Dict[int, List[Story]] = {}
        for story in all_stories:
            if story.user_id not in stories_by_user:
                stories_by_user[story.user_id] = []
            stories_by_user[story.user_id].append(story)

        grouped_stories = [
            stories_by_user[user_id]
            for user_id in user_ids
            if user_id in stories_by_user
        ]
        if page is not None:
            items_per_page = 30
            total_items = len(grouped_stories)
            total_pages = (total_items + items_per_page - 1) // items_per_page  # Округление вверх

            # Проверка на выход за границы
            if page < 1 or (page > total_pages and total_pages > 0):
                return [], None

            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            paginated_items = grouped_stories[start_idx:end_idx]

            paginator = Paginator(
                page=page,
                total=total_pages,
                total_count=total_items,
                has_prev=page > 1,
                has_next=page < total_pages
            )
            return paginated_items, paginator
        else:
            return grouped_stories, None

story = CRUDStory(Story)
