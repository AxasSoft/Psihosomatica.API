from typing import Optional, List
import logging

from fastapi import APIRouter, Depends, Query
from fastapi.params import Path, Header
from sqlalchemy.orm import Session
from starlette.requests import Request

from app import crud, models, schemas, getters, deps
from app.exceptions import UnprocessableEntity, UnfoundEntity, ListOfEntityError, InaccessibleEntity
from app.schemas import CreatingStory, UpdatingStory
from app.schemas.story import HugBody, HidingBody, IsFavoriteBody
from app.utils.response import get_responses_description_by_codes
from app.utils.cache import Cache

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get(
    '/short-stories/subscriptions/',
    response_model=schemas.Response[List[schemas.GettingUserStories]],
    name="Получить short-истории подписок",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
def get_short_stories_from_subscriptions(
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache_list),
):
    def fatch_short_stories_subscriptions():
        data, paginator = crud.story.get_short_stories_from_subscriptions(
            db,
            page=page,
            current_user=current_user,
        )

        return schemas.ListOfEntityResponse(
            data=[
                getters.story.get_grouped_short_story(db, datum, current_user)
                for datum
                in data
            ],
            paginator=paginator
        )


    key_tuple = ('short_stories_by_user',
                 f"user_subscriptions - {current_user.id} - page - {page} - grouped_by_users")
    data, from_cache = cache.behind_cache(key_tuple, fatch_short_stories_subscriptions, ttl=7200)
    
    if from_cache:
        logger.info("From the cache")
    else:
        logger.info("From the database")

    return data


@router.get(
    '/short-stories/',
    response_model=schemas.Response[List[schemas.GettingUserStories]],
    name="Получить все short-истории",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Истории"]
)
def get_short_stories(
        request: Request,
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: Optional[models.User] = Depends(deps.get_optional_current_user),
        x_real_ip: Optional[str] = Header(None),
        accept_language: Optional[str] = Header(None),
        user_agent: Optional[str] = Header(None),
        x_firebase_token: Optional[str] = Header(None),
        cache: Cache = Depends(deps.get_cache_list),

):
    def fatch_short_stories():
        data, paginator = crud.story.get_short_stories(
            db,
            page=page,
            current_user=current_user,
            host=request.client.host,
            x_real_ip=x_real_ip,
            accept_language=accept_language,
            user_agent=user_agent,
            x_firebase_token=x_firebase_token,
        )


        return schemas.ListOfEntityResponse(
            data=[
                getters.story.get_grouped_short_story(db, datum, current_user)
                for datum
                in data
            ],
            paginator=paginator
        )
    if current_user:
        key_tuple = ('short_stories_by_user', f"user - {current_user.id} - page - \
                     {page} - grouped_by_users")
    else:
        key_tuple = ('short_stories_by_user', f"page - \
                            {page} - grouped_by_users")
    data, from_cache = cache.behind_cache(key_tuple, fatch_short_stories, ttl=7200)


    if from_cache:
        logger.info("From the cache")
    else:
        logger.info("From the database")

    return data
