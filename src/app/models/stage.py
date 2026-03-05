from app.models import User
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.models.base_model import Base


class Stage(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)

    lessons = relationship("Lesson", back_populates="stage", lazy="selectin")
