import logging
from typing import List

from fastapi import APIRouter, Path, Query

from app import crud, schemas, deps, getters
from app.exceptions import raise_if_none
from app.utils.response import get_responses_description_by_codes

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/cp/stage/create/",
    response_model=schemas.response.Response[schemas.GettingStage],
    name="Создание этапа",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Административная панель / Этапы"],
)
async def create_stage_cp(
    data: schemas.CreatingStage,
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
):
    stage = await crud.stage.create(db=db, obj_in=data)
    await db.refresh(stage)
    stage_get = await getters.get_stage(db=db, stage=stage)

    return schemas.response.Response(
        data=stage_get,
    )


@router.delete(
    "/cp/stage/{stage_id}/",
    response_model=schemas.response.Response[None],
    name="Удаление этапа",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Административная панель / Этапы"],
)
async def delete_stage_cp(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
    stage_id: int = Path(...),
):
    await crud.stage.remove_by_id(db=db, id=stage_id)
    await db.commit()

    return schemas.response.Response(
        data=None,
    )


@router.patch(
    "/cp/stage/{stage_id}/",
    response_model=schemas.response.Response[schemas.GettingStage],
    name="Обновление этапа",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Административная панель / Этапы"],
)
async def update_stage_cp(
    data: schemas.UpdatingStage,
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
    stage_id: int = Path(...),
):
    stage = await crud.stage.get_by(db=db, id=stage_id)
    raise_if_none(stage, message="Этап не найден")

    stage = await crud.stage.update(db=db, db_obj=stage, obj_in=data)
    await db.commit()

    stage_get = await getters.get_stage(db=db, stage=stage)

    return schemas.response.Response(
        data=stage_get,
    )

@router.get(
    "/cp/stage/all/",
    response_model=schemas.response.Response[List[schemas.GettingStage]],
    name="Получение всех этапов",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Административная панель / Этапы"],
)
async def get_stages_cp(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
    page: int = Query(1),
):
    stages, paginator = await crud.stage.get_page(db=db, page=page)
    stages_get = [await getters.get_stage(db=db, stage=stage) for stage in stages]

    return schemas.response.Response(
        data=stages_get,
        paginator=paginator,
    )

@router.get(
    "/stage/all/",
    response_model=schemas.response.Response[List[schemas.GettingStage]],
    name="Получение всех этапов",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Этапы"],
)
async def get_stages(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveUserDependency,
    page: int = Query(1),
):
    stages, paginator = await crud.stage.get_page(db=db, page=page)
    stages_get = [await getters.get_stage(db=db, stage=stage) for stage in stages]

    return schemas.response.Response(
        data=stages_get,
        paginator=paginator,
    )

@router.get(
    "/cp/stage/{stage_id}/",
    response_model=schemas.response.Response[schemas.GettingStage],
    name="Получение этапа",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Административная панель / Этапы"],
)
async def get_stage_cp(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
    stage_id: int = Path(...),
):
    stage = await crud.stage.get(db=db, id=stage_id)
    raise_if_none(stage, message="Этап не найден")
    stage_get = await getters.get_stage(db=db, stage=stage)

    return schemas.response.Response(
        data=stage_get,
    )

@router.get(
    "/stage/{stage_id}/",
    response_model=schemas.response.Response[schemas.GettingStage],
    name="Получение этапа",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Этапы"],
)
async def get_stage(
    db: deps.DbDependency,
    current_user: deps.CurrentActiveUserDependency,
    stage_id: int = Path(...),
):
    stage = await crud.stage.get(db=db, id=stage_id)
    raise_if_none(stage, message="Этап не найден")
    stage_get = await getters.get_stage(db=db, stage=stage)

    return schemas.response.Response(
        data=stage_get,
    )
