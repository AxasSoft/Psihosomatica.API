import enum
from typing import Optional

from pydantic import BaseModel, Field


class GettingStoryAttachment(BaseModel):
    id: int
    main_link: str
    cover_link: Optional[str]
    is_image: bool
    created: int
