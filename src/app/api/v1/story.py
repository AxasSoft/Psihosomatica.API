from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from fastapi.params import Path, Header
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
import logging


from app import crud, models, schemas, getters, deps
from app.exceptions import UnprocessableEntity, UnfoundEntity, ListOfEntityError, InaccessibleEntity
from app.schemas import CreatingStory, UpdatingStory, HugBody, HidingBody, IsFavoriteBody, SetReaction
from app.utils.response import get_responses_description_by_codes
from app.utils.cache import Cache

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get(
    '/users/me/stories/',
    response_model=schemas.Response[List[schemas.GettingStory]],
    name="Получить все истории текущего пользователя",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
async def get_stories_by_user(
        db: AsyncSession = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: models.User = Depends(deps.get_current_active_user),
        is_hugged: Optional[bool] = Query(None),
        is_favorite: Optional[bool] = Query(None),
        is_short_story: Optional[bool] = Query(None),
        cache: Cache = Depends(deps.get_cache),
):

    async def fatch_stories():
        data, paginator = await crud.story.get_stories_by_user(
            db,
            user=current_user,
            page=page,
            current_user=current_user,
            is_hugged=is_hugged,
            is_favorite=is_favorite,
            is_short_story=is_short_story,
        )

        return schemas.Response(
            data=[await getters.story.get_story(db, datum, current_user) for datum in data],
            paginator=paginator
            )

    if is_short_story:
        key_tuple = ('short_stories_by_user', f"user_me - {current_user.id} - page - {page} - is_hugged - {is_hugged} - is_favorite - {is_favorite}")
    else:
        key_tuple = ('stories_by_user', f"user_me - {current_user.id} - page - {page} - is_hugged - {is_hugged} - is_favorite - {is_favorite}")
    data, from_cache = await cache.behind_cache(key_tuple, fatch_stories, ttl=7200)

    if from_cache:
        logger.info("From the cache")
    else:
        logger.info("From the database")

    return data


@router.get(
    '/stories/subscriptions/',
    response_model=schemas.Response[List[schemas.GettingStory]],
    name="Получить все истории текущего пользователя",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
async def get_stories_from_subscriptions(
        db: AsyncSession = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: models.User = Depends(deps.get_current_active_user),
        search: Optional[str] = Query(None, title="Текст истории, название хештега или темы"),
        is_hugged: Optional[bool] = Query(None),
        is_favorite: Optional[bool] = Query(None),
        is_short_story: Optional[bool] = Query(None),
        cache: Cache = Depends(deps.get_cache),
):
    async def fatch_stories_subscriptions():
        data, paginator = await crud.story.get_stories_from_subscriptions(
            db,
            page=page,
            current_user=current_user,
            search=search,
            is_hugged=is_hugged,
            is_favorite=is_favorite,
            is_short_story=is_short_story,
        )

        return schemas.Response(
            data=[
                await getters.story.get_story(db, datum, current_user)
                for datum
                in data
            ],
            paginator=paginator
        )

    if is_short_story:
        key_tuple = ('short_stories_by_user', f"user_me - {current_user.id} - page - {page} - is_hugged - {is_hugged} - is_favorite - {is_favorite}")
    else:
        key_tuple = ('stories_by_user', f"user_me - {current_user.id} - page - {page} - is_hugged - {is_hugged} - is_favorite - {is_favorite}")
    data, from_cache = await cache.behind_cache(key_tuple, fatch_stories_subscriptions, ttl=7200)
    
    if from_cache:
        logger.info("From the cache")
    else:
        logger.info("From the database")

    return data


@router.get(
    '/users/{user_id}/stories/',
    response_model=schemas.Response[List[schemas.GettingStory]],
    name="Получить все истории пользователя",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
async def get_stories_by_user(
        user_id: int = Path(...,title="Идентификатор пользователя"),
        db: AsyncSession = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        is_hugged: Optional[bool] = Query(None),
        is_favorite: Optional[bool] = Query(None),
        is_short_story: Optional[bool] = Query(None),
        current_user: Optional[models.User] = Depends(deps.get_current_active_user_or_none),
        cache: Cache = Depends(deps.get_cache),
):
    user = await crud.user.get(db, user_id)

    if user is None:
        raise UnfoundEntity(num=2, message="Пользователь не найден")

    async def fеtch_stories_user():
        data, paginator = await crud.story.get_stories_by_user(
            db,
            user=user,
            page=page,
            current_user=current_user,
            is_hugged=is_hugged,
            is_favorite=is_favorite,
            is_short_story=is_short_story
        )

        return schemas.Response(
            data=[
                await getters.story.get_story(db, datum,current_user)
                for datum
                in data
            ],
            paginator=paginator
        )
    if is_short_story:
        key_tuple = ('short_stories_by_user', f"user - {user.id} - page - {page} - is_hugged - {is_hugged} - is_favorite - {is_favorite}")
    else:
        key_tuple = ('stories_by_user', f"user - {user.id} - page - {page} - is_hugged - {is_hugged} - is_favorite - {is_favorite}")

    data, from_cache = await cache.behind_cache(key_tuple, fеtch_stories_user, ttl=7200)
    
    if from_cache:
        logger.info("From the cache")
    else:
        logger.info("From the database")

    return data

@router.get(
    '/cp/users/{user_id}/stories/',
    response_model=schemas.Response[List[schemas.GettingStory]],
    name="Получить все истории пользователя",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Административная панель / Истории"]
)
async def get_stories_by_users(
        user_id: int = Path(...,title="Идентификатор пользователя"),
        db: AsyncSession = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: Optional[models.User] = Depends(deps.get_current_active_su),
):
    user = await crud.user.get(db, user_id)

    if user is None:
        raise UnfoundEntity(num=2, message="Пользователь не найден")
    data, paginator = await crud.story.get_stories_by_user(db, user=user, page=page) 
    return schemas.Response(
        data=[
            await getters.story.get_story(db, datum,current_user)
            for datum
            in data
        ],
        paginator=paginator
    )


@router.post(
    '/stories/',
    response_model=schemas.Response[schemas.GettingStory],
    name="Добавить новую историю",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
async def add_new_story(
        data: CreatingStory,
        db: AsyncSession = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache),
):
    await cache.delete_by_prefix(f'short_stories_by_user')
    await cache.delete_by_prefix(f'stories_by_user')
    data, code, indexes = await crud.story.create_story_by_user(db, user=current_user, obj_in=data)

    if code == -2:
        raise ListOfEntityError(
            errors=[
                UnfoundEntity(
                    message='Изображение не найдено',
                    num=2,
                    path=f'$body.gallery[{index}]'
                )
                for index in indexes
            ],
            description='Изображения не найдены',
            http_status=404
        )

    if code == -3:
        raise ListOfEntityError(
            errors=[
                UnfoundEntity(
                    message='Изображение не принадлежит пользователю',
                    num=2,
                    path=f'$body.gallery[{index}]'
                )
                for index in indexes
            ],
            description='Изображения не принадлежат пользователю',
            http_status=403
        )

    if code == -4:
        raise ListOfEntityError(
            errors=[
                UnfoundEntity(
                    message='Изображение уже использовалось',
                    num=2,
                    path=f'$body.gallery[{index}]'
                )
                for index in indexes
            ],
            description='Изображения уже использовалось',
            http_status=422
        )

    if code == -5:
        raise UnfoundEntity(message='Видео не найдено', description='Видео не найдено',num=2)
    if code == -6:
        raise InaccessibleEntity(
            message='Видео не принадлежит пользователю',
            description='Видео не принадлежит пользователю'
        )
    if code == -7:
        raise UnprocessableEntity(
            message='Видео уже использовалось',
            description='Видео уже использовалось'
        )

    return schemas.Response(
        data=await getters.story.get_story(db, data, current_user)
    )


@router.post(
    '/cp/users/{user_id}/stories/',
    response_model=schemas.Response[schemas.GettingStory],
    name="Добавить новую историю",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Административная панель / Истории"]
)
async def add_new_story(
        data: CreatingStory,
        db: AsyncSession = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_su),
        user_id: int = Path(...,title="Идентификатор пользователя"),
        cache: Cache = Depends(deps.get_cache),
):
    await cache.delete_by_prefix(f'short_stories_by_user')
    await cache.delete_by_prefix(f'stories_by_user')

    user = await crud.user.get(db, user_id)
    if user is None:
        raise UnfoundEntity(num=2, message="Пользователь не найден")

    data, code, indexes = await crud.story.create_story_by_user(db, user=user, obj_in=data)


    if code == -2:
        raise ListOfEntityError(
            errors=[
                UnfoundEntity(
                    message='Изображение не найдено',
                    num=2,
                    path=f'$body.gallery[{index}]'
                )
                for index in indexes
            ],
            description='Изображения не найдены',
            http_status=404
        )

    if code == -3:
        raise ListOfEntityError(
            errors=[
                UnfoundEntity(
                    message='Изображение не пренадлежит пользователю',
                    num=2,
                    path=f'$body.gallery[{index}]'
                )
                for index in indexes
            ],
            description='Изображения не пренадлежат пользователю',
            http_status=403
        )

    if code == -4:
        raise ListOfEntityError(
            errors=[
                UnfoundEntity(
                    message='Изображение уже использовалось',
                    num=2,
                    path=f'$body.gallery[{index}]'
                )
                for index in indexes
            ],
            description='Изображения уже использовалось',
            http_status=422
        )

    if code == -5:
        raise UnfoundEntity(message='Видео не найдено', description='Видео не найдено',num=2)
    if code == -6:
        raise InaccessibleEntity(
            message='Видео не принадлежит пользователю',
            description='Видео не принадлежит пользователю'
        )
    if code == -7:
        raise UnprocessableEntity(
            message='Видео уже использовалось',
            description='Видео уже использовалось'
        )

    return schemas.Response(
        data= await getters.story.get_story(db, data, current_user)
    )


@router.put(
    '/stories/{story_id}/',
    response_model=schemas.Response[schemas.GettingStory],
    name="Изменить историю текущего пользователя",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
async def edit_story(
        data: UpdatingStory,
        story_id: int = Path(..., title="Идентификатор истории"),
        db: AsyncSession = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache),
):
    await cache.delete_by_prefix(f'short_stories_by_user')
    await cache.delete_by_prefix(f'stories_by_user')

    story = await crud.story.get(db, id=story_id)
    if story is None:
        raise UnfoundEntity(message="История не найдена", description="Исторрия не найдена",num=1)
    if story.user != current_user:
        raise InaccessibleEntity(
            message="История не принадлежит порльзователю",
            description="История не принадлежит порльзователю"
        )

    data, code, indexes = await crud.story.update(db, db_obj=story, obj_in=data)

    if code == -2:
        raise ListOfEntityError(
            errors=[
                UnfoundEntity(
                    message='Изображение не н6айдено',
                    num=2,
                    path=f'$body.gallery[{index}]'
                )
                for index in indexes
            ],
            description='Изображения не найдены',
            http_status=404
        )

    if code == -3:
        raise ListOfEntityError(
            errors=[
                UnfoundEntity(
                    message='Изображение не пренадлежит пользователю',
                    num=2,
                    path=f'$body.gallery[{index}]'
                )
                for index in indexes
            ],
            description='Изображения не пренадлежат пользователю',
            http_status=403
        )

    if code == -4:
        raise ListOfEntityError(
            errors=[
                UnfoundEntity(
                    message='Изображение уже использовалось',
                    num=2,
                    path=f'$body.gallery[{index}]'
                )
                for index in indexes
            ],
            description='Изображения уже использовалось',
            http_status=422
        )

    if code == -5:
        raise UnfoundEntity(
            message='Видео не найдено',
            description='Видео не найдено',
            num=2
        )
    if code == -6:
        raise InaccessibleEntity(
            message='Видео не принадлежит пользователю',
            description='Видео не принадлежит пользователю'
        )
    if code == -7:
        raise UnprocessableEntity(
            message='Видео уже использовалось',
            description='Видео уже использовалось'
        )

    return schemas.Response(
        data=await getters.story.get_story(db, data, current_user)
    )


@router.get(
    '/stories/{story_id}/',
    response_model=schemas.Response[schemas.GettingStory],
    name="Получить одну историю",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
async def get_story(
        story_id: int = Path(..., title="Идентификатор истории"),
        db: AsyncSession = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache),
):

    async def fatch_stories_single():
        story = await crud.story.get(db, id=story_id)
        if story is None:
            raise UnfoundEntity(message="История не найдена", description="Исторрия не найдена",num=1)

        return schemas.Response(
            data=await getters.story.get_story(db, story, current_user)
        )

    key_tuple = ('stories_by_user', f"story_id - {story_id}")
    data, from_cache = await cache.behind_cache(key_tuple, fatch_stories_single, ttl=7200)
    
    if from_cache:
        logger.info("From the cache")
    else:
        logger.info("From the database")

    return data


@router.put(
    '/cp/stories/{story_id}/',
    response_model=schemas.Response[schemas.GettingStory],
    name="Изменить историю текущего пользователя",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Административная панель / Истории"]
)
async def edit_story(
        data: UpdatingStory,
        story_id: int = Path(..., title="Идентификатор истории"),
        db: AsyncSession = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_su),
        cache: Cache = Depends(deps.get_cache),
):
    story = await crud.story.get(db, id=story_id)
    if story is None:
        raise UnfoundEntity(message="История не найдена", description="История не найдена",num=1)

    await cache.delete_by_prefix(f'short_stories_by_user')
    await cache.delete_by_prefix(f'stories_by_user')

    data, code, indexes = await crud.story.update(db, db_obj=story, obj_in=data)

    if code == -2:
        raise ListOfEntityError(
            errors=[
                UnfoundEntity(
                    message='Изображение не найдено',
                    num=2,
                    path=f'$body.gallery[{index}]'
                )
                for index in indexes
            ],
            description='Изображения не найдены',
            http_status=404
        )

    if code == -3:
        raise ListOfEntityError(
            errors=[
                UnfoundEntity(
                    message='Изображение не пренадлежит пользователю',
                    num=2,
                    path=f'$body.gallery[{index}]'
                )
                for index in indexes
            ],
            description='Изображения не пренадлежат пользователю',
            http_status=403
        )

    if code == -4:
        raise ListOfEntityError(
            errors=[
                UnfoundEntity(
                    message='Изображение уже использовалось',
                    num=2,
                    path=f'$body.gallery[{index}]'
                )
                for index in indexes
            ],
            description='Изображения уже использовалось',
            http_status=422
        )

    if code == -5:
        raise UnfoundEntity(
            message='Видео не найдено',
            description='Видео не найдено',
            num=2
        )
    if code == -6:
        raise InaccessibleEntity(
            message='Видео не принадлежит пользователю',
            description='Видео не принадлежит пользователю'
        )
    if code == -7:
        raise UnprocessableEntity(
            message='Видео уже использовалось',
            description='Видео уже использовалось'
        )

    return schemas.Response(
        data= await getters.story.get_story(db, data, current_user)
    )


@router.post(
    '/stories/{story_id}/viewed/',
    response_model=schemas.Response[schemas.GettingStory],
    name="Отметить историю как просмотренную текущим пользователем",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
async def mark_viewed(
        story_id: int = Path(..., title="Идентификатор истории"),
        db: AsyncSession = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    story = await crud.story.get(db, id=story_id)
    if story is None:
        raise UnfoundEntity(message="История не найдена", description="Исторрия не найдена", num=1)

    await crud.story.mark_story_as_viewed(db, story=story, user=current_user)

    return schemas.Response(
        data= await getters.story.get_story(db, story, current_user)
    )


@router.post(
    '/stories/{story_id}/hugged/',
    response_model=schemas.Response[schemas.GettingStory],
    name="Обнять историю",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
async def mark_hugged(
        hugbody: HugBody,
        story_id: int = Path(..., title="Идентификатор истории"),
        db: AsyncSession = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache),
):
    story = await crud.story.get(db, id=story_id)
    if story is None:
        raise UnfoundEntity(message="История не найдена", description="Исторрия не найдена",num=1)

    await cache.delete_by_prefix(f'short_stories_by_user')
    await cache.delete_by_prefix(f'stories_by_user')

    key_tuple_user = (f'user_me', f"user_me - {story.user_id}")
    await cache.delete(key_tuple_user)

    await crud.story.hug_story(db, story=story, user=current_user, hugs=hugbody.hugs)

    await db.refresh(story)

    return schemas.Response(
        data=await getters.story.get_story(db, story, current_user)
    )

@router.post(
    '/stories/{story_id}/set_reaction/',
    response_model=schemas.Response[schemas.GettingStory],
    name="Поставить или убрать реакцию истории",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
async def set_reaction(
        reaction_body: SetReaction,
        story_id: int = Path(..., title="Идентификатор истории"),
        db: AsyncSession = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache),
):
    story = await crud.story.get(db, id=story_id)
    if story is None:
        raise UnfoundEntity(message="История не найдена", description="Исторрия не найдена",num=1)

    await cache.delete_by_prefix(f'short_stories_by_user')
    await cache.delete_by_prefix(f'stories_by_user')

    key_tuple_user = (f'user_me', f"user_me - {story.user_id}")
    await cache.delete(key_tuple_user)

    await crud.story.react_story(db, story=story, user=current_user,
                           set_reaction=reaction_body.set_reaction, type_reaction=reaction_body.type_reaction)

    await db.refresh(story)

    return schemas.Response(
        data=await getters.story.get_story(db, story, current_user)
    )

@router.post(
    '/stories/{story_id}/is-favorite/',
    response_model=schemas.Response[schemas.GettingStory],
    name="Добавить или убрать историю из избранного",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
async def mark_favorite(
        favbody: IsFavoriteBody,
        story_id: int = Path(..., title="Идентификатор истории"),
        db: AsyncSession = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache),
):
    await cache.delete_by_prefix('stories_by_user')
    key_tuple_user = ('user_me', f"user_me - {current_user.id}")
    await cache.delete(key_tuple_user)
    story = await crud.story.get(db, id=story_id)
    if story is None:
        raise UnfoundEntity(message="История не найдена", description="История не найдена",num=1)

    await cache.delete_by_prefix(f'short_stories_by_user')
    await cache.delete_by_prefix(f'stories_by_user')

    await crud.story.favorite_story(db, story=story, user=current_user,is_favorite=favbody.is_favorite)

    return schemas.Response(
        data=await getters.story.get_story(db, story, current_user)
    )


@router.post(
    '/stories/{story_id}/is-hidden/',
    response_model=schemas.Response[None],
    name="Скрыть историю",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
async def mark_hidden(
        hiding_body: HidingBody,
        story_id: int = Path(..., title="Идентификатор истории"),
        db: AsyncSession = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache),
):
    key_tuple_user = ('user_me', f"user_me - {current_user.id}")
    await cache.delete(key_tuple_user)
    story = await crud.story.get(db, id=story_id)
    if story is None:
        raise UnfoundEntity(message="История не найдена", description="Исторрия не найдена",num=1)
    await cache.delete_by_prefix(f'short_stories_by_user')
    await cache.delete_by_prefix(f'stories_by_user')

    await crud.story.hide_story(db, story=story, user=current_user,hide=hiding_body.hiding)

    return schemas.Response(data=None)


@router.delete(
    '/stories/{story_id}/',
    response_model=schemas.Response[None],
    name="Удалить историю текущего пользователя",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
async def delete_profile_story(
        story_id: int = Path(...,title="Идентификатор истории"),
        db: AsyncSession = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache),
):
    key_tuple_user = ('user_me', f"user_me - {current_user.id}")
    await cache.delete(key_tuple_user)
    story = await crud.story.get(db, id=story_id)
    if story is None:
        raise UnfoundEntity(
            message="История не найдена",
            description="Исторрия не найдена",
            num=1
        )

    if story.user != current_user:
        raise InaccessibleEntity(
            message="История не принадлежит порльзователю",
            description="История не принадлежит порльзователю"
        )

    await cache.delete_by_prefix(f'short_stories_by_user')
    await cache.delete_by_prefix(f'stories_by_user')

    await crud.story.remove(db, id=story_id)
    return schemas.Response(data=None)


@router.delete(
    '/cp/stories/{story_id}/',
    response_model=schemas.Response[None],
    name="Удалить историю",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Административная панель / Истории"]
)
async def delete_user_story(
        story_id: int = Path(...,title="Идентификатор истории"),
        db: AsyncSession = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_su),
        cache: Cache = Depends(deps.get_cache),
):
    await cache.delete_by_prefix('stories_by_user')
    story = await crud.story.get(db, id=story_id)
    if story is None:
        raise UnfoundEntity(message="История не найдена", description="Исторрия не найдена",num=1)

    await cache.delete_by_prefix(f'short_stories_by_user')
    await cache.delete_by_prefix(f'stories_by_user')

    await crud.story.remove(db,id=story_id)
    return schemas.Response(data=None)


@router.get(
    '/stories/',
    response_model=schemas.Response[List[schemas.GettingStory]],
    name="Получить все истории по теме, хештегу и пользователю",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
async def get_stories_by_criteria(
        request: Request,
        db: AsyncSession = Depends(deps.get_db),
        user_id: Optional[int] = Query(None, title="Идентификатор пользователя"),
        hashtag_id: Optional[int] = Query(None, title="Идентификатопр хештега"),
        search: Optional[str] = Query(None, title="Текст истории, название хештега или темы"),
        is_hugged: Optional[bool] = Query(None),
        is_favorite: Optional[bool] = Query(None),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: Optional[models.User] = Depends(deps.get_current_active_user_or_none),
        cache: Cache = Depends(deps.get_cache),
): 
    if user_id is not None:
        user = await crud.user.get(db,user_id)
        if user is None:
            raise UnfoundEntity(description="Пользователь не найден", message="Пользователь не найден", num=2)
    else:
        user = None

    if hashtag_id is not None:
        hashtag = await crud.hashtag.get(db, hashtag_id)
        if hashtag is None:
            raise UnfoundEntity(description="Хештег не найден", message="Хештег не найден", num=2)
    else:
        hashtag = None
    async def fatch_stories_criteria():
        if current_user is not None:
            data, paginator = await crud.story.get_stories(
                db,
                user=user,
                hashtag=hashtag,
                page=page,
                current_user=current_user,
                search=search,
                is_hugged=is_hugged,
                is_favorite=is_favorite
            )
        else:
            data, paginator = await crud.story.get_stories(
                db,
                user=user,
                hashtag=hashtag,
                page=page,
                current_user=current_user,
                search=search,
            )

        return schemas.Response(
            data=[
                await getters.story.get_story(db, datum, current_user)
                for datum
                in data
            ],
            paginator=paginator
        )
    

    key_tuple = ('stories_by_user', f"user - {current_user.id} - page - \
                 {page} - is_hugged - {is_hugged} - is_favorite - {is_favorite} - user_id - {user_id} - \
                 hashtag_id - {hashtag_id} - search - {search}")
    data, from_cache = await cache.behind_cache(key_tuple, fatch_stories_criteria, ttl=7200)
    
    if from_cache:
        logger.info("From the cache")
    else:
        logger.info("From the database")

    return data
