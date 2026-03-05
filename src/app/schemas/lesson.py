from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List

from app.enums import TypeAnswer
from .task import GettingTask


class BaseLesson(BaseModel):
    name: str = Field(...)
    description: str = Field(...)

    stage_id: int = Field(...)


class CreatingLesson(BaseLesson):
    pass


class UpdatingLesson(BaseModel):
    name: str | None = Field(None)
    description: str | None = Field(None)

    stage_id: int | None = Field(None)


class GettingLessonShort(BaseLesson):
    id: int = Field(...)


class GettingLesson(GettingLessonShort):
    tasks: List[GettingTask] | None = Field([])


