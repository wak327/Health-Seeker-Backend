from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


class InvalidTokenError(Exception):
    """Custom exception raised when an access token cannot be decoded or validated."""


def create_access_token(
    subject: Union[str, int],
    *,
    secret_key: str,
    algorithm: str,
    expires_delta: Optional[timedelta] = None,
    default_expiry_minutes: int = 60,
) -> str:
    """Return an encoded JWT access token for the given subject."""

    if isinstance(subject, int):
        subject = str(subject)

    now = datetime.now(timezone.utc)
    expires_delta = expires_delta or timedelta(minutes=default_expiry_minutes)
    expire = now + expires_delta

    to_encode = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def decode_access_token(
    token: str,
    *,
    secret_key: str,
    algorithm: str,
) -> dict[str, Any]:
    """Decode a JWT access token and validate its signature/expiry."""

    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    except JWTError as exc:
        raise InvalidTokenError("Could not validate credentials") from exc
    return payload
