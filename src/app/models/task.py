from app.models import User
from sqlalchemy import Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.models.base_model import Base
from app.enums import TypeAnswer


class Task(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    type: Mapped[TypeAnswer] = mapped_column(Enum(TypeAnswer))
    photo: Mapped[str | None] = mapped_column(String, nullable=True)

    lesson_id: Mapped[int] = mapped_column(ForeignKey("lesson.id", ondelete="SET NULL"), index=True, nullable=True)
    lesson = relationship("Lesson", back_populates="tasks", lazy="joined")

