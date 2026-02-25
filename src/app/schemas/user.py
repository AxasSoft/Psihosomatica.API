
from pydantic import BaseModel, Field, EmailStr, field_validator

from app.enums import Gender


class BaseUser(BaseModel):
    first_name: str = Field(..., title='Имя')
    last_name: str | None = Field(None, title="Фамилия")
    patronymic: str | None = Field(None, title="Отчество")
    phone: str | None  = Field(None)
    age: int | None = Field(None)
    weight: int | None = Field(None)
    level: int | None = Field(None)


class RegistrationUser(BaseUser):
    gender: Gender
    city: str | None = None


class CreatingUser(RegistrationUser):
    email: EmailStr | None = Field(None, title='Email')
    phone: str | None = Field(None)
    password: str = Field(..., title="Пароль")


class CreatingUserForCP(CreatingUser):
    password: str | None = Field(None, title="Пароль")
    gender: Gender | None = Field(None)
    is_superuser: bool | None = Field(False)
    phone: str


class SignInBodyForCP(BaseModel):
    email_or_username: EmailStr | str
    password: str


class UpdatingUser(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    patronymic: str| None = None
    gender: Gender | None = None
    city: str | None = None


class UpdatingUserForCP(UpdatingUser):
    is_superuser: bool | None = None
    is_admin: bool | None = None
    password: str | None = None
    phone: str | None = None
    email: EmailStr | None = Field(None, title='Email')


class BaseGettingUser(BaseUser):
    id: int
    first_name: str | None
    last_name: str | None
    patronymic: str| None
    gender: Gender | None
    email: EmailStr | None
    phone: str | None
    is_superuser: bool


class GettingUser(BaseGettingUser):
    pass


class TokenWithUser(BaseModel):
    user: BaseGettingUser = Field(...)
    token: str = Field(...)


class ChangePassword(BaseModel):
    old_password: str
    new_password: str