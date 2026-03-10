import enum
from typing import Optional, List, Dict, Tuple

from pydantic import BaseModel, Field

from .story_attachment import GettingStoryAttachment
from .hashtag import GettingHashtag
from .user import GettingUser
from app.enums.reaction import ReactionType


class CreatingStory(BaseModel):
    text: Optional[str]
    title: Optional[str]
    video: Optional[int]
    gallery: Optional[List[int]]
    is_private: Optional[bool] = Field(False)
    is_short_story: Optional[bool] = Field(False)
    hashtags: List[str]


class UpdatingStory(BaseModel):
    text: Optional[str]
    title: Optional[str]
    video: Optional[int]
    gallery: Optional[List[int]]
    is_private: Optional[bool]
    is_short_story: Optional[bool]
    hashtags: Optional[List[str]]


class GettingStory(BaseModel):
    id: int
    created: int
    user: GettingUser
    title: Optional[str]
    text: Optional[str]
    video: Optional[GettingStoryAttachment]
    gallery: List[GettingStoryAttachment]
    is_private: bool
    is_short_story: bool
    hashtags: List[GettingHashtag]
    views_count: int = 0
    viewed: Optional[bool] = None
    hugs_count: int = 0
    hugged: Optional[bool] = None
    is_favorite: Optional[bool] = None
    comments_count: int = 0
    is_comment: Optional[bool] = False
    reactions_count: Dict[str, int] = {}
    reacted: Dict[str, bool] = {}


class GettingUserStories(BaseModel):
    user: GettingUser
    stories: List[GettingStory]


class HugBody(BaseModel):
    hugs: bool = Field(..., title="Обнять",
                       description="Флаг, означающий поставновление(`true`) или снятие (`false`) отмеки \"Обнять\"")


class SetReaction(BaseModel):
    set_reaction: bool = Field(..., title="Реакцию поставить",
                       description="Флаг, означающий поставновление(`true`) или снятие (`false`) реакции")
    type_reaction: ReactionType = Field(..., title="Тип реакции",)


class IsFavoriteBody(BaseModel):
    is_favorite: bool = Field(...)


class HidingBody(BaseModel):
    hiding: bool = Field(..., title="Скрыть", description="Флаг, означающий. скрыта ли история")
