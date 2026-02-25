from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, cast, text, Select, desc

from app.crud import AsyncCRUDBase
from app.models import VerificationCode
from app.services.gsms_tg_sender import gsms_tg_sender
from app.schemas import CreatingVerificationCode, UpdatingVerificationCode, VerifyingCode


class CRUDVerificationCode(AsyncCRUDBase[VerificationCode, CreatingVerificationCode, UpdatingVerificationCode]):
    async def create(self, db: AsyncSession, *, obj_in: CreatingVerificationCode) -> VerificationCode:

        code = gsms_tg_sender.send(tel=obj_in.tel)
        verification_code = VerificationCode(tel=obj_in.tel, value=code)
        db.add(verification_code)
        await db.commit()
        await db.refresh(verification_code)
        return verification_code
    
    async def check_verification_code(self, db: AsyncSession, *, data: VerifyingCode) -> int:
        stmt = (select(self.model)
                .filter(self.model.tel == data.phone)
                .order_by(self.model.used, desc(self.model.created))
                .limit(1))
        result = await db.execute(stmt)
        code = result.scalars().first()

        if code is None or data.code != code.value:
            return -3
        if code.used:
            return -1
        if datetime.now(timezone.utc) - code.created > timedelta(minutes=5):
            return -2
        if data.code != code.value:
            return -3
        else:
            code.used = True
            db.add(code)
            await db.commit()
            return 0


verification_code = CRUDVerificationCode(VerificationCode)
