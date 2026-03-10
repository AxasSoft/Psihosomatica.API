import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from app.models.base_model import Base
from .user import User
from .story import Story
from app.enums.reaction import ReactionType


class Reaction(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False, index=True)
    story_id = Column(Integer, ForeignKey(Story.id), nullable=False, index=True)
    type_reaction = Column(
        SAEnum(
            ReactionType,
            name="reaction_type_enum",
        ),
        nullable=False,
    )

    user = relationship(User, back_populates='reactions')
    story = relationship(Story, back_populates='reactions')
