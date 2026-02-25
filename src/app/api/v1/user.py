import logging
from typing import List

from fastapi import APIRouter, Depends, status, UploadFile, File, Body, Path, Query, Header

from app import crud, models, schemas, deps, getters
from app.exceptions import InaccessibleEntity, UnprocessableEntity, raise_if_none
from app.utils.response import get_responses_description_by_codes

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/cp/users/create/admin/",
    response_model=schemas.response.Response[schemas.GettingUser],
    name="Создание пользователя",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Административная панель / Пользователь"],
)
async def sign_user_cp(
    data: schemas.CreatingUserForCP,
    db: deps.DbDependency,
    current_user: deps.CurrentActiveSuperUserDependency,
):
    is_email = await crud.user.get_by(db=db, email=data.email) if data.email else None
    is_phone = await crud.user.get_by(db=db, phone=data.phone)

    if is_email:
        raise UnprocessableEntity(message="Пользователь с таким емейл уже есть")
    if is_phone:
        raise UnprocessableEntity(message="Пользователь с таким номером телефона уже есть")

    user = await crud.user.registration(db=db, data=data)

    return schemas.response.Response(
        data=await getters.get_user(db=db, user=user),
    )

@router.get(
    '/cp/users/all/',
    response_model=schemas.Response[List[schemas.GettingUser]],
    tags=['Административная панель / Пользователь'],
    name="Получить всех пользователей",
    responses=get_responses_description_by_codes([400, 401, 422]),
)
async def get_all_user(
        db: deps.DbDependency,
        current_user: deps.CurrentActiveSuperUserDependency,
        is_active: bool = Query(True),
        page: int | None = Query(None),
        q: str | None = Query(None),
        order_by: str | None = Query(None, description="Если хотите получить объекты в обратном порядке, то поставьте '-' перед названием "),
):
    user_all, paginator = await crud.user.get_users_page(
        db=db,
        ex_id=current_user.id,
        page=page,
        is_active=is_active,
        q=q,
        order_by=order_by,
    )

    users = [await getters.get_user(db=db, user=user) for user in user_all]

    return schemas.Response(
        data=users,
        paginator=paginator,
    )

@router.get(
    '/cp/users/me/',
    response_model=schemas.Response[schemas.GettingUser],
    tags=['Административная панель / Пользователь'],
    name="Получить текущего пользователя",
    responses=get_responses_description_by_codes([400, 401, 422]),
)
@router.get(
    '/users/me/',
    response_model=schemas.Response[schemas.GettingUser],
    name="Получить текущего пользователя",
    tags=['Пользователь'],
    responses=get_responses_description_by_codes([400, 401, 422]),
)
async def get_current_user_endpoint(
        db: deps.DbDependency,
        current_user: deps.CurrentActiveUserDependency
):
    return schemas.Response[schemas.GettingUser](
        data=await getters.get_user(db=db, user=current_user)
    )

@router.get(
    '/cp/users/{user_id}/',
    response_model=schemas.Response[schemas.GettingUser],
    tags=['Административная панель / Пользователь'],
    name="Получить пользователя",
    responses=get_responses_description_by_codes([400, 401, 422]),
)
@router.get(
    '/users/{user_id}/',
    response_model=schemas.Response[schemas.GettingUser],
    tags=['Пользователь'],
    name="Получить пользователя",
    responses=get_responses_description_by_codes([400, 401, 422]),
)
async def get_user_by_id(
        db: deps.DbDependency,
        user_id: int = Path(...),
):
    user = await crud.user.get_by(db=db, id=user_id)
    raise_if_none(user)

    return schemas.Response[schemas.GettingUser](
        data=await getters.get_user(db=db, user=user)
    )

@router.patch(
    '/cp/users/{user_id}/update/',
    response_model=schemas.Response[schemas.GettingUser],
    tags=['Административная панель / Пользователь'],
    name="Обновить пользователя",
    responses=get_responses_description_by_codes([400, 401, 422]),
)
async def update_user_admin(
        db: deps.DbDependency,
        data: schemas.UpdatingUserForCP,
        current_user: deps.CurrentActiveSuperUserDependency,
        user_id: int = Path(...),
):
    is_email_user = await crud.user.get_by(db=db, email=data.email) if data.email else None
    is_phone_user = await crud.user.get_by(db=db, phone=data.phone) if data.phone else None

    if is_email_user and is_email_user.id != user_id:
        raise UnprocessableEntity(message="Пользователь с таким емейл уже есть")
    if is_phone_user and is_phone_user.id != user_id:
        raise UnprocessableEntity(message="Пользователь с таким номером телефона уже есть")

    user = await crud.user.get_by(db=db, id=user_id)
    raise_if_none(user)

    user_for_return = await crud.user.update(db=db, db_obj=user, obj_in=data)

    return schemas.Response[schemas.GettingUser](
        data=await getters.get_user(db=db, user=user_for_return)
    )

@router.patch(
    '/cp/users/me/update/',
    response_model=schemas.Response[schemas.GettingUser],
    name="Обновить текущего пользователя",
    tags=['Административная панель / Пользователь'],
    responses=get_responses_description_by_codes([400, 401, 422]),
)
@router.patch(
    '/users/me/update/',
    response_model=schemas.Response[schemas.GettingUser],
    name="Обновить текущего пользователя",
    tags=['Пользователь'],
    responses=get_responses_description_by_codes([400, 401, 422]),
)
async def update_user(
        db: deps.DbDependency,
        data: schemas.UpdatingUser,
        cache: deps.CacheDependency,
        current_user: models.User = Depends(deps.get_current_active_su)
):
    user = await crud.user.update(db=db, db_obj=current_user, obj_in=data)
    await cache.delete_by_prefix(f"user:{user.id}")
    return schemas.Response[schemas.GettingUser](
        data=await getters.get_user(db=db, user=user)
    )

@router.delete(
    '/cp/users/{user_id}/delete/',
   response_model=schemas.Response[None],
    name="Удалить пользователя",
    tags=['Административная панель / Пользователь'],
    responses=get_responses_description_by_codes([400, 401, 422]),
)
async def delete_user(
        db: deps.DbDependency,
        current_user: deps.CurrentActiveSuperUserDependency,
        user_id: int = Path(...),
):
    user = await crud.user.get_by(db=db, id=user_id)
    raise_if_none(user)

    await crud.user.delete_user(db=db, user=user)
    await db.delete(user)
    await db.commit()
    return schemas.Response[None](
        data=None
    )

@router.delete(
    '/cp/users/{user_id}/deactivate/',
   response_model=schemas.Response[None],
    name="Деактивировать пользователя",
    tags=['Административная панель / Пользователь'],
    responses=get_responses_description_by_codes([400, 401, 422]),
)
async def deactivate_user_cp(
        db: deps.DbDependency,
        current_user: deps.CurrentActiveSuperUserDependency,
        user_id: int = Path(...),
):
    user = await crud.user.get_by(db=db, id=user_id)
    raise_if_none(user)

    await crud.user.delete_firebase(db=db, user=user)
    await crud.user.delete_user(db=db, user=user)
    return schemas.Response[None](
        data=None
    )

@router.delete(
    '/users/me/delete/',
   response_model=schemas.Response[None],
    name="Деактивировать текущего пользователя",
    tags=['Пользователь'],
    responses=get_responses_description_by_codes([400, 401, 422]),
)
async def deactivate_user(
        db: deps.DbDependency,
        current_user: models.User = Depends(deps.get_current_active_su),
        x_firebase_token: str | None = Header(None),
):
    await crud.user.delete_firebase(db=db, user=current_user)
    await crud.user.delete_user(db=db, user=current_user)
    return schemas.Response[None](
        data=None
    )

@router.post(
    '/users/me/sign_out/',
    response_model=schemas.Response[None],
    name="Выйти с аккаунта",
    tags=['Пользователь'],
    responses=get_responses_description_by_codes([400, 401, 422]),
    description="Удаляет FireBase token устройства из БД если его передать, иначе ничего не делает"
)
async def sign_out_user(
        db: deps.DbDependency,
        current_user: models.User = Depends(deps.get_current_active_su),
        x_firebase_token: str | None = Header(None),
):
    if x_firebase_token is not None:
        await crud.user.sign_out(db=db, x_firebase_token=x_firebase_token)

    return schemas.Response(data=None)

@router.put(
    "/cp/users/change_password/",
    response_model=schemas.response.Response[None],
    tags=['Административная панель / Пользователь'],
    name="Изменение своего пароля",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
)
async def update_password_current_user(
        data: schemas.ChangePassword,
        db: deps.DbDependency,
        current_user: models.User = Depends(deps.get_current_active_su),
):
    await crud.user.change_password(db=db, data=data, user=current_user)

    return schemas.response.Response(data=None)