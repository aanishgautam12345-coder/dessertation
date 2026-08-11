"""Security utilities - password hashing and JWT token creation/verification."""

import logging
import os
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.config import get_settings

logger = logging.getLogger(__name__)

# Use bcrypt with explicit rounds to avoid passlib/bcrypt 5.x compatibility issues
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def _truncate(password: str) -> str:
    """Bcrypt silently ignores bytes beyond 72. Truncate explicitly to avoid errors."""
    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    return pwd_context.hash(_truncate(password))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_truncate(plain), hashed)


def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    to_encode = {**data, "exp": expire, "iat": datetime.now(timezone.utc)}
    to_encode.setdefault("purpose", "access")
    # Add jti (JWT ID) for token revocation support
    import uuid
    to_encode["jti"] = str(uuid.uuid4())
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


def get_token_jti(token: str) -> str | None:
    """Extract the jti claim from a token without verifying signature.
    Used for blacklist checks."""
    try:
        from jose import jwt as jose_jwt
        unverified = jose_jwt.get_unverified_claims(token)
        return unverified.get("jti")
    except Exception:
        return None
