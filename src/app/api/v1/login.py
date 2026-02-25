import logging

from fastapi import APIRouter, Depends, Header, Request
from fastapi.security import OAuth2PasswordRequestForm

from app import crud, models, schemas, deps, getters
from app.exceptions import InaccessibleEntity, UnprocessableEntity
from app.utils.response import get_responses_description_by_codes
from app.deps import update_visit_date

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/login/access-token/",
    response_model=schemas.TokenSchema,
    tags=["Вход"],
    name="Войти по емейл и паролю - только swagger",
    responses=get_responses_description_by_codes([400, 401, 422]),
)
async def login_access_token(
        request: Request,
        db: deps.DbDependency,
        form_data: OAuth2PasswordRequestForm = Depends(),
        x_real_ip: str | None = Header(None),
        accept_language: str | None = Header(None),
        user_agent: str | None = Header(None),
        x_firebase_token: str | None = Header(None),
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await crud.user.authenticate(
        db,
        email_or_username=form_data.username,
        password=form_data.password,
        host=request.client.host,
        x_real_ip=x_real_ip,
        accept_language=accept_language,
        user_agent=user_agent,
        x_firebase_token=x_firebase_token
    )
    if not user:
        raise UnprocessableEntity(
            message="Неверный логин или пароль",
            description="Неверный логин или пароль",
            num=0
        )
    elif not await crud.user.is_active(user):
        raise UnprocessableEntity(
            message="Пользователь не активирован",
            description="Неверный логин или пароль",
            num=1
        )
    await update_visit_date(db=db, user=user)
    access_token = await crud.user.get_token(user=user)
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.post(
    '/cp/sign-in/',
    response_model=schemas.response.Response[schemas.TokenWithUser],
    name="Войти по email и постоянному паролю или по имени и паролю",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Вход"]
)
async def sign_in_cp(
        request: Request,
        data: schemas.user.SignInBodyForCP,
        db: deps.DbDependency,
        x_real_ip: str | None = Header(None),
        accept_language: str | None = Header(None),
        user_agent: str | None = Header(None),
        x_firebase_token: str | None = Header(None),
):
    user = await crud.user.authenticate(
        db,
        email_or_username=data.email_or_username,
        password=data.password,
        host=request.client.host,
        x_real_ip=x_real_ip,
        accept_language=accept_language,
        user_agent=user_agent,
        x_firebase_token=x_firebase_token
    )
    if user is None:
        raise InaccessibleEntity(message='Неверный логин или пароль')

    access_token = await crud.user.get_token(user=user)
    return schemas.response.Response(
        data=schemas.TokenWithUser(
            user=await getters.get_user(db=db, user=user),
            token=access_token
        )
    )

@router.post(
    '/sign-in/',
    response_model=schemas.response.Response[schemas.TokenWithUser],
    name="Войти по номеру телефона и коду подтверждения",
    responses=get_responses_description_by_codes([400, 401, 422]),
    tags=["Вход"],
)
async def sign_in(
        request: Request,
        data: schemas.VerifyingCode,
        db: deps.DbDependency,
        x_real_ip: str | None = Header(None),
        accept_language: str | None = Header(None),
        user_agent: str | None = Header(None),
        x_firebase_token: str | None = Header(None),
):
    code = await crud.verification_code.check_verification_code(db=db, data=data)
    #if code == -3:
    #    raise UnprocessableEntity(message='Код не отправлялся на этот номер телефона', num=0)
    if code == -1:
        raise UnprocessableEntity(message='Код уже использован', num=1)
    if code == -2:
        raise UnprocessableEntity(message='Время жизни кода истекло', num=2)
    if code == -3:
        raise UnprocessableEntity(message='Код подтверждения не совпадает', num=2)

    user = await crud.crud_user.user.create_or_get_by_tel(db=db, tel=data.phone)
    await crud.crud_user.user.handle_device(
        db=db,
        owner=user,
        host=request.client.host,
        x_real_ip=x_real_ip,
        accept_language=accept_language,
        user_agent=user_agent,
        x_firebase_token=x_firebase_token
    )
    token = await crud.crud_user.user.get_token(user=user)
    return schemas.response.Response(
        data=schemas.TokenWithUser(
            user=await getters.get_user(db=db, user=user),
            token=token
        )
    )
