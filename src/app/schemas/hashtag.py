import enum
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field



class BaseHashtag(BaseModel):
    text: str


class GettingHashtag(BaseHashtag):
    id: int = Field(...)
    stories_count: int = Field(0, title="Количество историй")
    cover: Optional[str] = Field(None)

class CreatingHashtag(BaseHashtag):
    pass


class UpdatingHashtag(BaseHashtag):
    pass

