import logging
from typing import List

from fastapi import APIRouter, Depends, status, UploadFile, File, Body, Path, Query, Header

from app import crud, models, schemas, deps, getters
from app.exceptions import InaccessibleEntity, UnprocessableEntity, raise_if_none
from app.utils.response import get_responses_description_by_codes

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/cp/lesson/create/",
    response_model=schemas.response.Response[schemas.GettingLesson],
    name="Создание урока",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Административная панель / Уроки"],
)
async def create_lesson(
    data: schemas.CreatingLesson,
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
):
    stage_id = data.stage_id
    stage = crud.stage.get(db=db, id=stage_id)
    raise_if_none(stage, message="Этап не найден")

    lesson = await crud.lesson.create(db=db, obj_in=data)
    await db.commit()
    await db.refresh(lesson)
    lesson_get = await getters.get_lesson(db=db, lesson=lesson)

    return schemas.response.Response(
        data=lesson_get,
    )

@router.delete(
    "/cp/lesson/{lesson_id}/",
    response_model=schemas.response.Response[None],
    name="Удаление урока",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Административная панель / Уроки"],
)
async def delete_lesson(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
    lesson_id: int = Path(...),
):
    await crud.lesson.remove_by_id(db=db, id=lesson_id)

    return schemas.response.Response(
        data=None,
    )

@router.patch(
    "/cp/lesson/{lesson_id}/",
    response_model=schemas.response.Response[schemas.GettingLesson],
    name="Обновление урока",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Административная панель / Уроки"],
)
async def update_lesson(
    data: schemas.UpdatingLesson,
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
    lesson_id: int = Path(...),
):
    lesson = await crud.lesson.get_by(db=db, id=lesson_id)
    raise_if_none(lesson, message="Урок не найден")

    lesson_get = await crud.lesson.update(db=db, db_obj=lesson, obj_in=data)
    return schemas.response.Response(
        data=lesson_get,
    )

@router.get(
    "/lesson/all/",
    response_model=schemas.response.Response[List[schemas.GettingLesson]],
    name="Получение всех уроков",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Уроки"],
)
async def get_lessons(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveUserDependency,
    page: int = Query(1),
):
    lessons, paginator = await crud.lesson.get_page(db=db, page=page)
    lesson_get = [await getters.get_lesson(db=db, lesson=lesson) for lesson in lessons]

    return schemas.response.Response(
        data=lesson_get,
        paginator=paginator
    )

@router.get(
    "/cp/lesson/all/",
    response_model=schemas.response.Response[List[schemas.GettingLesson]],
    name="Получение всех уроков",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Административная панель / Уроки"],
)
async def get_lessons(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
    page: int = Query(1),
):
    lessons, paginator = await crud.lesson.get_page(db=db, page=page)
    lesson_get = [await getters.get_lesson(db=db, lesson=lesson) for lesson in lessons]

    return schemas.response.Response(
        data=lesson_get,
        paginator=paginator
    )

@router.get(
    "/lesson/{lesson_id}/",
    response_model=schemas.response.Response[schemas.GettingLesson],
    name="Получение одного урока",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Уроки"],
)
async def get_lesson(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
    lesson_id: int = Path(...),
):
    lesson = await crud.lesson.get(db=db, id=lesson_id)
    lessons_get = await getters.get_lesson(db=db, lesson=lesson)

    return schemas.response.Response(
        data=lessons_get,
    )

@router.get(
    "/cp/lesson/{lesson_id}/",
    response_model=schemas.response.Response[schemas.GettingLesson],
    name="Получение одного урока",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Административная панель / Уроки"],
)
async def get_lesson(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
    lesson_id: int = Path(...),
):
    lesson = await crud.lesson.get(db=db, id=lesson_id)
    lessons_get = await getters.get_lesson(db=db, lesson=lesson)

    return schemas.response.Response(
        data=lessons_get,
    )

