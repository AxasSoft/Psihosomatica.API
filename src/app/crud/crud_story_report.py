from typing import Any, Optional, Type, List, Tuple
from app.models import Story
from app.schemas.response import Paginator
from app.utils import pagination

from sqlalchemy import String, or_, func, desc
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import AsyncCRUDBase
from app.models.user import User

from ..models import StoryReport
from ..schemas.story_report import CreatingStoryReport, UpdatingStoryReport


class CRUDStoryReport(AsyncCRUDBase[StoryReport, CreatingStoryReport, UpdatingStoryReport]):

    async def get_multi(
            self, db: AsyncSession, *, page: Optional[int] = None
    ) -> Tuple[List[StoryReport], Paginator]:

        query = select(StoryReport).order_by(StoryReport.is_satisfy != None, desc(StoryReport.created))

        return await pagination.get_page_async(db, query, page)

    async def create_for_users(self, db: AsyncSession, *, obj_in: CreatingStoryReport,subject:User,object_:Story):
        report = StoryReport()
        report.object_ = object_
        report.subject = subject
        report.additional_text = obj_in.additional_text
        report.reason = obj_in.reason
        db.add(report)
        await db.commit()
        await db.refresh(report)
        return report


story_report = CRUDStoryReport(StoryReport)
