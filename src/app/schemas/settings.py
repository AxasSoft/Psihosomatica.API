from pydantic import BaseModel, Field


class SettingsGetting(BaseModel):
    price_for_premium: int


class SettingsCreate(BaseModel):
    pass


class SettingsUpdate(BaseModel):
    price_for_premium: int | None

