from app.models import User
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.models.base_model import Base


class Lesson(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)

    stage_id: Mapped[int] = mapped_column(ForeignKey("stage.id"), index=True)
    stage = relationship("Stage", back_populates="lessons", lazy="joined")

    tasks = relationship("Task", back_populates="lesson", lazy="selectin")
