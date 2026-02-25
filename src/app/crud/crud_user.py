from typing import Any, Dict, List
import logging

from sqlalchemy import select, func, and_, or_, cast, text, Select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession
from user_agents import parse

from app import models, schemas
from app.crud.async_base import AsyncCRUDBase
from app.models import User, Device, FirebaseToken
from app.utils import pagination, security
from app.utils.security import get_password_hash, verify_password
from app.utils.datetime import to_unix_timestamp, from_unix_timestamp
from app.exceptions import InaccessibleEntity
from app.utils.datetime import utcnow

logger = logging.getLogger(__name__)

class CRUDUser(AsyncCRUDBase[User, schemas.CreatingUser, schemas.UpdatingUser]):
    async def _adapt_fields(
        self, obj: dict[str, Any] | models.Base, **kwargs
    ) -> dict[str, Any]:
        fields = await super(CRUDUser, self)._adapt_fields(obj, **kwargs)
        if "email" in fields:
            fields["email"] = (
                fields["email"].lower()
                if isinstance(fields["email"], str)
                else fields["email"]
            )
        if "password" in fields and fields["password"] is not None:
            fields["hashed_password"] = get_password_hash(fields.pop("password"))
        if "birthdate" in fields and isinstance(fields["birthdate"], int):
            fields["birthdate"] = (from_unix_timestamp(fields.pop("birthdate")))
        return fields

    async def _handle_device(
            self,
            db: AsyncSession,
            owner: User,
            host: str | None = None,
            x_real_ip: str | None = None,
            accept_language: str | None = None,
            user_agent: str | None = None,
            x_firebase_token: str | None = None,
    ):
        stmt = (
            select(Device)
            .where(
                Device.user_id == owner.id,
                Device.ip_address == host,
                Device.x_real_ip == x_real_ip,
                Device.accept_language == accept_language,
                Device.user_agent == user_agent,
            )
            .order_by(desc(Device.created))
            .limit(1)
        )

        result = await db.execute(stmt)
        device: Device | None = result.scalar_one_or_none()

        detected_os: str | None = None

        if user_agent:
            ua_object = parse(str(user_agent))
            detected_os = ua_object.os.family

            if not detected_os or detected_os.lower() == "other":
                if "okhttp" in user_agent.lower():
                    detected_os = "Android"
                elif "cfnetwork" in user_agent.lower():
                    detected_os = "iOS"
                else:
                    detected_os = None

        if device is None:
            device = Device(
                user=owner,
                ip_address=host,
                x_real_ip=x_real_ip,
                accept_language=accept_language,
                user_agent=user_agent,
                detected_os=detected_os,
            )
            db.add(device)
        if x_firebase_token:
            stmt = select(FirebaseToken).where(FirebaseToken.value==x_firebase_token)
            result = await db.execute(stmt)
            firebase = result.scalars().first()
            if firebase is not None:
                await db.delete(firebase)

            firebase_token = FirebaseToken(device=device, value=x_firebase_token)
            db.add(firebase_token)

        await db.commit()

    async def handle_device(
            self,
            db: AsyncSession,
            owner: User,
            host: str | None = None,
            x_real_ip: str | None = None,
            accept_language: str | None = None,
            user_agent: str | None = None,
            x_firebase_token: str | None = None,
    ):
        return await self._handle_device(
            db=db,
            owner=owner,
            host=host,
            x_real_ip=x_real_ip,
            accept_language=accept_language,
            user_agent=user_agent,
            x_firebase_token=x_firebase_token
        )

    async def authenticate_by_phone(
            self,
            db: AsyncSession,
            *,
            phone: str,
            host: str | None = None,
            x_real_ip: str | None = None,
            accept_language: str | None = None,
            user_agent: str | None = None,
            x_firebase_token: str | None = None,
    ) -> User | None:
        user = await self.get_by_tel(db, tel=phone)
        if not user:
            return None

        await self._handle_device(
            db=db,
            owner=user,
            host=host,
            x_real_ip=x_real_ip,
            accept_language=accept_language,
            user_agent=user_agent,
            x_firebase_token=x_firebase_token,
        )

        return user

    async def authenticate(
            self,
            db: AsyncSession,
            *,
            email_or_username: str,
            password: str,
            host: str | None = None,
            x_real_ip: str | None = None,
            accept_language: str | None = None,
            user_agent: str | None = None,
            x_firebase_token: str | None = None,
    ) -> User | None:
        user = await self.get_by_email(db, email=email_or_username.lower())
        if not user:
            user = await self.get_by(db, first_name=email_or_username.lower())
            if not user:
                return None

        if not verify_password(password, user.hashed_password):
            return None

        await self._handle_device(
            db=db,
            owner=user,
            host=host,
            x_real_ip=x_real_ip,
            accept_language=accept_language,
            user_agent=user_agent,
            x_firebase_token=x_firebase_token,
        )

        return user

    async def registration(self, db: AsyncSession, data: schemas.RegistrationUser) -> User:
        data = await self._adapt_fields(data.model_dump())
        user = await super(CRUDUser, self).create(db=db, obj_in=data)

        await db.commit()
        return user

    async def get_by_email(self, db: AsyncSession, *, email: str) -> User | None:
        stmt = select(self.model).where(self.model.email == email.lower())
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_tel(self, db: AsyncSession, *, tel: str) -> User | None:
        stmt = select(self.model).where(self.model.phone == tel)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_get_by_tel(self, db: AsyncSession, tel: str):
        model = self.model
        stmt = select(model).where(model.phone == tel)
        result = await db.execute(stmt)
        user = result.scalars().first()

        if user is None:
            user = User()
            user.phone = tel

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def delete_user(self, db: AsyncSession, *, user: User):
        user.is_active = False

        logging.info(f'Почта {user.email} и телефон {user.phone} откреплены для пользователя {user.id}')
        user.email = None
        user.phone = None
        await db.commit()
        await db.refresh(user)

    async def get_users_page(
        self,
        db: AsyncSession,
        ex_id: int,
        q: str | None = None,
        order_by: str | None = None,
        page: int | None = None,
        is_active: bool = True,
        size: int = 30,
        **kwargs,
    ):
        stmt = (select(self.model)
                .filter(self.model.id != ex_id)
                .filter(self.model.is_active == is_active)
                )
        stmt = self._filters(stmt, kwargs)

        if q:
            ilike_pattern = f"%{q}%"
            stmt = stmt.filter(
                or_(
                    self.model.phone.ilike(ilike_pattern),
                    self.model.first_name.ilike(ilike_pattern),
                    self.model.last_name.ilike(ilike_pattern),
                    self.model.patronymic.ilike(ilike_pattern),
                )
            )

        stmt = self._orders(stmt, order_by)
        return await pagination.get_page_async(db, stmt, page, size)

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        obj_in: schemas.UpdatingUser | Dict[str, Any],
        **kwargs,
    ) -> User:
        obj_in = await self._adapt_fields(obj_in)
        await super(CRUDUser, self).update(db=db, db_obj=db_obj, obj_in=obj_in, **kwargs)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_ids_active(self, db: AsyncSession) -> list[int]:
        stmt = select(User.id).filter(User.is_active)
        user_ids = (await db.execute(stmt)).scalars().all()
        return user_ids

    async def get_token(self, user: User):
        return security.create_token(subject=user.id)

    async def is_active(self, user: User) -> bool:
        return user.is_active

    async def sign_out(self, db: AsyncSession, x_firebase_token: str ) -> None:
        stmt = delete(FirebaseToken).where(FirebaseToken.value == x_firebase_token)
        await db.execute(stmt)
        await db.commit()

    async def delete_firebase(self, db: AsyncSession, user: User):
        stmt = (
            delete(FirebaseToken)
            .where(
                FirebaseToken.device_id.in_(
                    select(Device.id).where(Device.user_id == user.id)
                )
            )
        )

        await self.session.execute(stmt)
        await self.session.commit()

    async def change_password(self, db: AsyncSession, data: schemas.ChangePassword, user: User) -> User:
        if not verify_password(
            data.old_password, user.hashed_password
        ):
            raise InaccessibleEntity(message=f'Пароль неправильный')

        user.hashed_password = get_password_hash(data.new_password)

        db.add(user)
        await db.commit()

        return user

user = CRUDUser(User)