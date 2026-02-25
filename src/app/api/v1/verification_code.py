
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, models, schemas, deps
from app.utils.response import get_responses_description_by_codes
from app.schemas import GettingVerificationCode

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    '/verification-codes/',
    response_model=schemas.Response[schemas.GettingVerificationCode],
    name="Оправить код подтверждения",
    responses=get_responses_description_by_codes([400, 401, 403, 422]),
    tags=["Вход"]
)
async def send_code(
        data: schemas.verification_code.CreatingVerificationCode,
        db: Session = Depends(deps.get_db),
):
    code = await crud.verification_code.create(db=db, obj_in=data)
    return schemas.Response(data=GettingVerificationCode.model_validate(code))
