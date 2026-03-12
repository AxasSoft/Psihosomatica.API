from pydantic import BaseModel, Field


class SettingsGetting(BaseModel):
    price_premium: int


class SettingsCreate(BaseModel):
    pass


class SettingsUpdate(BaseModel):
    price_premium: int | None

