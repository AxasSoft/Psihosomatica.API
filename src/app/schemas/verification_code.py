import re

from pydantic import BaseModel, Field, field_validator

from app.config import settings
from app.exceptions import UnprocessableEntity

class CreatingVerificationCode(BaseModel):
    tel: str = Field(...,title="Телефон")


class UpdatingVerificationCode(BaseModel):
    pass


class GettingVerificationCode(BaseModel):
    value: str

    class Config:
        from_attributes = True


class VerifyingCode(BaseModel):
    phone: str = Field(...,title="Телефон")
    code: str = Field(...,title="Код подтверждения")