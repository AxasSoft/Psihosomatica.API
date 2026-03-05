from app.crud import AsyncCRUDBase
from app.models import Lesson
from app.schemas import CreatingLesson, UpdatingLesson


class CRUDLesson(AsyncCRUDBase[Lesson, CreatingLesson, UpdatingLesson]):
    pass


lesson = CRUDLesson(Lesson)
