from typing import Union, Dict, Any, Optional, Tuple, List

from app.crud import AsyncCRUDBase
from app.models.hashtag import Hashtag
from app.schemas.hashtag import CreatingHashtag, UpdatingHashtag
from app.schemas.response import Paginator
from app.utils import pagination
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession


class CRUDHashtag(AsyncCRUDBase[Hashtag, CreatingHashtag, UpdatingHashtag]):

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Hashtag,
        obj_in: Union[UpdatingHashtag, Dict[str, Any]]
    ) -> Hashtag:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        return await super().update(db,db_obj=db_obj,obj_in=update_data)

    async def search(
            self,
            db: AsyncSession,
            *,
            search: Optional[str],
            page: Optional[int] = None
    ) -> Tuple[List[Hashtag], Paginator]:
        stmt = select(Hashtag)
        if search is not None:
            stmt = stmt.where(Hashtag.text.ilike(f"%{search}%"))
        stmt = stmt.order_by(Hashtag.text)
        return await pagination.get_page_async(db, stmt, page)


hashtag = CRUDHashtag(Hashtag)
