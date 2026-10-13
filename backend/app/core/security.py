from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

password_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def _create_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str,
    token_version: int = 0,
) -> str:
    expires_at = datetime.now(timezone.utc) + expires_delta
    claims = {
        "sub": subject,
        "exp": expires_at,
        "type": token_type,
        "ver": token_version,
    }
    return jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str, token_version: int = 0) -> str:
    return _create_token(
        subject,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "access",
        token_version,
    )


def create_refresh_token(subject: str, token_version: int = 0) -> str:
    return _create_token(
        subject,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "refresh",
        token_version,
    )


def decode_access_token(token: str) -> dict:
    claims = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if claims.get("type") != "access":
        raise JWTError("Invalid token type")
    return claims


def decode_refresh_token(token: str) -> dict:
    claims = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if claims.get("type") != "refresh":
        raise JWTError("Invalid token type")
    return claims
