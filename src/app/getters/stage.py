from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.getters.universal import transform
from app.models import Stage
from app.schemas import GettingStage
from .lesson import get_lesson_short

async def get_stage(db: AsyncSession, stage: Stage) -> GettingStage:
    return transform(
        stage,
        GettingStage,
        lessons = [await get_lesson_short(db, lesson) for lesson in stage.lessons] if stage.lessons else [],
    )


