from app.getters.universal import transform
from app.models import Settings
from app.schemas import SettingsGetting

async def get_settings(settings: Settings) -> SettingsGetting:
    return transform(
        settings,
        SettingsGetting,
    )

