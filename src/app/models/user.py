from datetime import date, datetime
from sqlalchemy import Boolean, Integer, String, Date, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import Base
from app.enums import Gender

def get_full_name(user):
    return (" ".join([item for item in [user.first_name, user.patronymic, user.last_name] if item is not None])).strip()

class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    patronymic: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(15), index=True, unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    last_visited: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    level: Mapped[int] = mapped_column(Integer, nullable=True)
    weight: Mapped[int] = mapped_column(Integer, nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    create: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )

    devices = relationship(
        "Device",
        cascade="all, delete-orphan",
        back_populates="user",
    )

    devices = relationship("Device", cascade="all, delete-orphan", back_populates="user", lazy="dynamic")
    stories = relationship("Story", cascade="all, delete-orphan", back_populates="user", lazy="dynamic")
    stories_attachments = relationship("StoryAttachment", cascade="all, delete-orphan", back_populates="user")
    story_hidings = relationship('StoryHiding', cascade="all, delete-orphan", back_populates="user", lazy="dynamic")
    views = relationship("View", cascade="all, delete-orphan", back_populates="user")
    hugs = relationship("Hug", cascade="all, delete-orphan", back_populates="user")
    reactions = relationship("Reaction", cascade="all, delete-orphan", back_populates="user")
    favorite_stories = relationship("FavoriteStory", cascade="all, delete-orphan", back_populates="user")
    comments = relationship("Comment", cascade="all, delete-orphan", back_populates="user", lazy='dynamic')
    subject_story_reports = relationship('StoryReport', cascade="all, delete-orphan", back_populates="subject",
                                         lazy="selectin")
    subject_subscriptions = relationship('Subscription', cascade="all, delete-orphan", back_populates="subject",
                                         foreign_keys='Subscription.subject_id', lazy='selectin')
    object_subscriptions = relationship('Subscription', cascade="all, delete-orphan", back_populates="object_",
                                        lazy="joined", foreign_keys='Subscription.object_id')
    subject_user_blocks = relationship('UserBlock', cascade="all, delete-orphan", back_populates="subject",
                                       lazy="selectin", foreign_keys='UserBlock.subject_id')
    object_user_blocks = relationship('UserBlock', cascade="all, delete-orphan", back_populates="object_",
                                      lazy="selectin", foreign_keys='UserBlock.object_id')