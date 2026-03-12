import logging

from sqlalchemy import select

from app.crud import AsyncCRUDBase
from app.models import Settings
from app.schemas import SettingsCreate, SettingsUpdate

logger = logging.getLogger(__name__)

class CRUDSetting(AsyncCRUDBase[Settings, SettingsCreate, SettingsUpdate]):

    async def get_price_from_db(self,db: AsyncCRUDBase):
        settings = await db.execute(select(Settings).where(Settings.id == 1))
        return settings.scalars().first().price_premium

settings = CRUDSetting(Settings)
