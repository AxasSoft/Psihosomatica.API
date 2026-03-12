import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud import AsyncCRUDBase
from app.models import User, Payment
from app.schemas import PaymentCreate, PaymentUpdate
from app.services.payment import TinkoffPayment

logger = logging.getLogger(__name__)

class CRUDPayment(AsyncCRUDBase[Payment, PaymentCreate, PaymentUpdate]):
    async def make_payment(
            self,
            db: AsyncSession,
            payment: Payment,
            user: User,
    ):
        logger.debug("Начало оплаты")
        payment_bank = TinkoffPayment(
            user=user,
            amount=payment.amount,
            os=payment.os,
            order_id=payment.uuid,
        )

        payment_response = payment_bank.make_payment()
        logger.debug("payment response: %s", payment_response)
        payment.pay_link = payment_response.get("pay_link")
        payment.payment_id = payment_response.get("payment_id")
        await db.commit()

        return payment.pay_link


    async def get_payment(
            self,
            db: AsyncSession,
            order_id: uuid.UUID,
    ):
        stmt = select(Payment).where(Payment.uuid==order_id)
        res = await db.execute(stmt)
        return res.unique().scalar_one_or_none()

payment = CRUDPayment(Payment)
