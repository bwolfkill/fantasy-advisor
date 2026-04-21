from datetime import UTC, datetime, timedelta

from jwt import decode, encode
from pwdlib import PasswordHash

from app.core.config import settings

pwd_hasher = PasswordHash.recommended()


def hash_password(plain: str) -> str:
    return pwd_hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_hasher.verify(plain, hashed)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (
        expires_delta if expires_delta else timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    )
    payload = {"sub": subject, "exp": expire}
    return encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> str:
    return decode(token, settings.SECRET_KEY, algorithms=["HS256"])
