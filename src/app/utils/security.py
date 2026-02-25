import random
import uuid
from datetime import datetime, timedelta
from string import ascii_letters, digits
from typing import Any

from app.config import settings
from app.utils.datetime import utcnow
from cryptography.fernet import Fernet
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def generate_digital_code(n: int) -> str:
    return f"{random.randint(1, 10 ** n + 1):0100d}"[-n:]


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return decoded_token["email"]
    except jwt.JWTError:
        return


def generate_random_code(length: int, digits_only: bool = False) -> str:
    """
    Генерирует стороку, содержащую пароль

    :length: длина генерируемой строки
    :digits_only: только цифры
    :return: псевдослучайная строка, составленная из латинских букв в нижнем и верхнем регистре и цифр заданной длины
    """
    if digits_only:
        result = "".join(random.choices(digits, k=length))
    else:
        result = "".join(random.choices(digits + ascii_letters, k=length))
    return result


def create_token(
    subject: Any,
    expires_delta: timedelta | None = None,
    token_type: str | None = None,
    nbf: datetime | None = None,
    jti: str | None = None,
    **extra_args,
) -> str:
    now = utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    claim_extra_fields: list[str] = getattr(settings, "TOKEN_FIELDS", [])
    to_encode: dict[str, Any] = {"sub": str(subject), **extra_args}
    if "exp" in claim_extra_fields:
        to_encode["exp"] = expire
    if "iat" in claim_extra_fields:
        to_encode["iat"] = now
    if "nbf" in claim_extra_fields:
        to_encode["nbf"] = nbf if nbf is not None else now
    if "jti" in claim_extra_fields:
        to_encode["jti"] = jti if jti is not None else str(uuid.uuid4())
    if token_type is not None:
        to_encode["type"] = token_type
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def encrypt(s: str) -> str:
    f = Fernet(settings.CRYPT_KEY.encode())
    return f.encrypt(s.encode()).decode()


def decrypt(s: str) -> str:
    f = Fernet(settings.CRYPT_KEY.encode())
    try:
        return f.decrypt(s).decode()

    except Exception:
        return s
