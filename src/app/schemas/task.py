from pydantic import BaseModel, Field, EmailStr, field_validator

from app.enums import TypeAnswer

class BaseTask(BaseModel):
    name: str = Field(...)
    description: str = Field(...)
    type: TypeAnswer = Field(...)
    photo: str | None = Field(None)

    lesson_id: int | None = Field(None)


class CreatingTask(BaseTask):
    pass


class UpdatingTask(BaseModel):
    name: str | None = Field(None)
    description: str | None = Field(None)
    type: TypeAnswer | None = Field(None)
    photo: str | None = Field(None)

    lesson_id: int | None = Field(None)


class GettingTask(BaseTask):
    id: int = Field(...)
