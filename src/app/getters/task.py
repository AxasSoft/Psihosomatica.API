from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.getters.universal import transform
from app.models import Task
from app.schemas import GettingTask

async def get_task(db: AsyncSession, task: Task) -> GettingTask:
    return transform(
        task,
        GettingTask,
    )


