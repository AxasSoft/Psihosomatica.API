from fastapi import APIRouter
from app import schemas, models, deps, getters, crud
from app.exceptions import raise_if_none
from app.utils.response import get_responses_description_by_codes

router_admin = APIRouter(prefix="/cp/settings", tags=["Административная панель / Настройки"])
router_user = APIRouter(prefix="/settings", tags=["Настройки"])

@router_user.get(
    "/",
    response_model=schemas.Response[schemas.SettingsGetting],
    name="Получить настройки",
    responses=get_responses_description_by_codes([400, 403, 404, 422]),
)
@router_admin.get(
    "/",
    response_model=schemas.Response[schemas.SettingsGetting],
    name="Получить настройки",
    responses=get_responses_description_by_codes([400, 403, 404, 422]),
)
async def get_settings(
        db: deps.DbDependency,
):
    settings = await crud.settings.get(db, 1)
    raise_if_none(settings, "Настройки не найдены")

    data = await getters.get_settings(settings)

    return schemas.Response(data=data)

@router_admin.patch(
    "/",
    response_model=schemas.Response[schemas.SettingsGetting],
    name="Обновить настройки",
    responses=get_responses_description_by_codes([400, 403, 404, 422]),
)
async def update_settings(
        data: schemas.SettingsUpdate,
        db: deps.DbDependency,
        current_user: deps.CurrentActiveSuperUserDependency,
):
    settings = await crud.settings.get(db, 1)
    raise_if_none(settings, "Настройки не найдены")

    updated = await crud.object.update(db=db, db_obj=settings, obj_in=data)

    return schemas.Response(
        data=await getters.get_settings(updated)
    )

router = APIRouter()
router.include_router(router_admin)
router.include_router(router_user)