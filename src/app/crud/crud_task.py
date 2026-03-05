from app.crud import AsyncCRUDBase
from app.models import Task
from app.schemas import CreatingTask, UpdatingTask


class CRUDTask(AsyncCRUDBase[Task, CreatingTask, UpdatingTask]):
    pass


task = CRUDTask(Task)
