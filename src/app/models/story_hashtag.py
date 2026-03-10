import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base_model import Base
from .user import User
from .story import Story
from .hashtag import Hashtag


class StoryHashtag(Base):
    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey(Story.id), nullable=True, index=True)
    hashtag_id = Column(Integer, ForeignKey(Hashtag.id), nullable=True, index=True)

    story = relationship(Story, back_populates='story_hashtags')
    hashtag = relationship(Hashtag, back_populates='hashtag_stories',lazy='joined')

