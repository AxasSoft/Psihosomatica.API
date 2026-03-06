from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.getters.universal import transform
from app.models import Lesson
from app.schemas import GettingLesson, GettingLessonShort
from .task import get_task


async def get_lesson(db: AsyncSession, lesson: Lesson) -> GettingLesson:
    return transform(
        lesson,
        GettingLesson,
        tasks = [await get_task(db, task) for task in lesson.tasks] if lesson.tasks else [],
    )

async def get_lesson_short(db: AsyncSession, lesson: Lesson) -> GettingLessonShort:
    return transform(
        lesson,
        GettingLessonShort,
    )
