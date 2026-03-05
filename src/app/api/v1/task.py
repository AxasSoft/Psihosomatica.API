import logging
from typing import List

from fastapi import APIRouter, Path, Query

from app import crud, schemas, deps
from app.exceptions import raise_if_none
from app.utils.response import get_responses_description_by_codes

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/cp/task/create/",
    response_model=schemas.response.Response[schemas.GettingTask],
    name="Создание задания",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Административная панель / Задания"],
)
async def create_task(
    data: schemas.CreatingTask,
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
):
    lesson = await crud.lesson.get(db=db, id=data.lesson_id)
    raise_if_none(lesson, message="Урок не найден")

    task = await crud.task.create(db=db, obj_in=data)

    return schemas.response.Response(
        data=task,
    )


@router.delete(
    "/cp/task/{task_id}/",
    response_model=schemas.response.Response[None],
    name="Удаление задания",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Административная панель / Задания"],
)
async def delete_task(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
    task_id: int = Path(...),
):
    await crud.task.remove_by_id(db=db, id=task_id)

    return schemas.response.Response(
        data=None,
    )


@router.patch(
    "/cp/task/{task_id}/",
    response_model=schemas.response.Response[schemas.GettingTask],
    name="Обновление задания",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Административная панель / Задания"],
)
async def update_task(
    data: schemas.UpdatingTask,
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
    task_id: int = Path(...),
):
    task = await crud.task.get_by(db=db, id=task_id)
    raise_if_none(task, message="Задание не найдено")

    task = await crud.task.update(db=db, db_obj=task, obj_in=data)

    return schemas.response.Response(
        data=task,
    )

@router.get(
    "/task/all/",
    response_model=schemas.response.Response[List[schemas.GettingTask]],
    name="Получение всех заданий",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Задания"],
)
async def get_tasks(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveUserDependency,
    page: int = Query(1),
):
    tasks, paginator = await crud.task.get_page(db=db, page=page)

    return schemas.response.Response(
        data=tasks,
        paginator=paginator,
    )

@router.get(
    "/task/all/",
    response_model=schemas.response.Response[List[schemas.GettingTask]],
    name="Получение всех заданий",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Задания"],
)
async def get_tasks(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveUserDependency,
    page: int = Query(1),
):
    tasks, paginator = await crud.task.get_page(db=db, page=page)

    return schemas.response.Response(
        data=tasks,
        paginator=paginator,
    )

@router.get(
    "/cp/task/{task_id}/",
    response_model=schemas.response.Response[schemas.GettingTask],
    name="Получение задания",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Задания"],
)
async def get_task_cp(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveUserDependency,
    task_id: int = Path(...),
):
    task = await crud.task.get(db=db, id=task_id)
    raise_if_none(task, message="Задание не найдено")

    return schemas.response.Response(
        data=task,
    )

@router.get(
    "/task/{task_id}/",
    response_model=schemas.response.Response[schemas.GettingTask],
    name="Получение задания",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Задания"],
)
async def get_task(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveUserDependency,
    task_id: int = Path(...),
):
    task = await crud.task.get(db=db, id=task_id)
    raise_if_none(task, message="Задание не найдено")

    return schemas.response.Response(
        data=task,
    )