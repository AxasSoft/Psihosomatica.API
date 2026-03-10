from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base_model import Base
from .user import User
from .story import Story


class Comment(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=True, default=datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False, index=True)
    story_id = Column(Integer, ForeignKey(Story.id), nullable=False, index=True)

    text = Column(String(), nullable=True)

    user = relationship("User",  back_populates='comments')
    story = relationship("Story", back_populates='comments')
