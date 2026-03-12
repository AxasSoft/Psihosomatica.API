import logging
from datetime import timedelta

from fastapi import APIRouter, Response

from app import crud, deps, models, schemas, enums
from app.utils.datetime import utcnow
from app.exceptions import InaccessibleEntity, UnprocessableEntity, raise_if_none
from app.utils.response import get_responses_description_by_codes
from app.services.etg_ostrovok_manager.etg_ostrovok_manager import ostrovok_manager, PICT_SIZE
from app.exceptions import raise_if_none
from app.services.celery.tasks import check_booking_status_task
from app.enums import HotelBookingStatus


router = APIRouter()

logger = logging.getLogger(__name__)

@router.post(
    "/callback/tinkoff/",
    tags=["Банк / Подтверждение"],
    name="Уведомление  обратного вызова для TinkoffPay",
    responses=get_responses_description_by_codes([401, 403, 400]),
)
async def tinkoff_callback(
    data: schemas.payment.TinkoffNotificationPayment,
    db: deps.DbDependency,
    #notificator: Notificator = Depends(deps.get_notificator),
    #redis_cache: RedisCache = Depends(deps.get_redis_cache)
):
    """URL на веб-сайте Мерчанта, куда будет отправлен POST запрос о статусе выполнения
    вызываемых методов. Только для методов Authorize, FinishAuthorize, Confirm, Cancel
    [help]: https://www.tbank.ru/kassa/dev/payments/"""

    logger.info("data: %s", data)
    payment = None

    if data.status == "CONFIRMED" and data.success:
        payment = await crud.payment.get_payment(db=db, order_id=data.order_id)
        raise_if_none(payment, message="Заказ не найден")

        if not payment.is_pay:
            payment.is_pay = True
            payment.pay_date = utcnow()

            if payment.user_id is not None:
                user = await crud.user.get(db=db, id=payment.user_id)
                raise_if_none(user, message="Пользотвалеь не найден")
                user.is_premium = True

    # возврат чека
    if data.status == "RECEIPT" and data.success:
        payment = await crud.payment.get_payment(db=db, order_id=data.order_id) if payment is None else payment
        raise_if_none(payment, message="Заказ не найден")
        payment.ofd_url = data.url

    await db.commit()
    return Response(content="OK")


"""
Tinkoff
Ответ на HTTP(s)-нотификацию
В случае успешной обработки нотификации Мерчанту необходимо вернуть ответ 
HTTP CODE = 200 с телом сообщения: OK (без тегов и заглавными английскими буквами).
Если ответ «OK» не получен, нотификация считается неуспешной, и сервис будет повторно 
отправлять данную нотификацию раз в час в течение 24 часов. Если нотификация за это 
время не доставлена, она будет сложена в архив.
При получении нотификации и перед её обработкой настоятельно рекомендуем проверить подпись запроса.
"""

