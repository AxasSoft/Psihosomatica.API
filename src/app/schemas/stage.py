from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List

from app.enums import TypeAnswer
from app.schemas import GettingLesson, GettingLessonShort


class BaseStage(BaseModel):
    name: str = Field(...)


class CreatingStage(BaseStage):
    pass


class UpdatingStage(BaseModel):
    name: str | None = Field(None)


class GettingStage(BaseStage):
    id: int = Field(...)
    lessons: List[GettingLessonShort] | None = Field([])
