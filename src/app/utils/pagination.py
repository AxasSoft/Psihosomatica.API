import logging

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.response import Paginator


async def get_page_async(
    db: AsyncSession,
    select_stmt: Select,
    page: int | None = None,
    size: int | None = None,
    scalars: bool = True,
) -> tuple[list, Paginator | None]:
    paginator = None
    if page:
        if size is None or size > 1000:
            size = 30
        count_stmt = select(func.count()).select_from(select_stmt.subquery())
        item_count = (await db.scalars(count_stmt)).one()
        logging.info(f"{item_count=}")
        page_count = ((item_count - 1) // size) + 1
        paginator = Paginator(
            page=page,
            total=page_count,  # кол-во страниц
            has_prev=page > 1,
            has_next=page < page_count,
        )
        offset = (page - 1) * size
        select_stmt = select_stmt.offset(offset).limit(size)
    items = (await db.execute(select_stmt)).unique()
    if scalars:
        items = items.scalars()
    return items.all(), paginator


async def get_page_async_no_total(
    db: AsyncSession,
    select_stmt: Select,
    page: int | None = None,
    size: int | None = None,
    scalars: bool = True,
):
    size = 30 if size is None or size > 1000 else size
    offset = (page - 1) * size
    select_stmt = select_stmt.offset(offset).limit(size)
    items = (await db.execute(select_stmt)).unique()
    if scalars:
        items = items.scalars()
    paginator = Paginator(
        page=page,
        total=None,
        has_prev=page > 1,
        has_next=None,
    )
    return items.all(), paginator


def paginate(items: list, page: int = 1, page_size: int = 30) -> Paginator:
    total_items = len(items)

    total_pages = (total_items + page_size - 1) // page_size

    if page > total_pages:
        page = total_pages
    if page < 1:
        page = 1

    start = (page - 1) * page_size
    end = start + page_size

    paginated_items = items[start:end]

    has_prev = page > 1
    has_next = page < total_pages

    paginator = Paginator(
        page=page,
        total=total_pages,
        has_prev=has_prev,
        has_next=has_next,
    )

    return paginated_items, paginator

def get_page_no_db(elements: list, page: int | None = None) -> Paginator:
    if page is None:
        return elements, None

    items_per_page=30
    total = (len(elements) + (items_per_page - 1)) // items_per_page
    if 0 < page <= total:
        list_elements = elements[items_per_page*(page - 1):items_per_page*page]
    else:
        list_elements = []


    paginator = Paginator(
        page=page,
        total=total,
        has_prev=page > 1,
        has_next=page < total
    )
    return list_elements, paginator