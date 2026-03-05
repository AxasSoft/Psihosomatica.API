from app.crud import AsyncCRUDBase
from app.models import Stage
from app.schemas import CreatingStage, UpdatingStage


class CRUDStage(AsyncCRUDBase[Stage, CreatingStage, UpdatingStage]):
    pass


stage = CRUDStage(Stage)
