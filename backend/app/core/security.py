"""
Security utilities — password hashing and JWT management.

This module is the single place for all cryptographic operations.
Nothing outside this module should ever touch raw passwords or
sign/verify tokens directly.

Design decisions:
- bcrypt for password hashing: industry standard, slow by design
  (makes brute force attacks expensive)
- JWT for stateless auth: no server-side session storage needed
- Separate access + refresh tokens: short-lived access tokens
  limit the damage window if a token is stolen
- Token type claim: prevents access tokens being used as refresh
  tokens and vice versa
"""

from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# ----------------------------------------------------------------
# Password hashing
# CryptContext manages the hashing algorithm and handles
# migrations to stronger algorithms transparently.
# ----------------------------------------------------------------
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Work factor — increase over time as hardware improves
)


def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    Returns the hash string to store in the database.
    Never store the plain_password — discard it after hashing.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a stored hash.
    Returns True if they match, False otherwise.
    Uses constant-time comparison to prevent timing attacks.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ----------------------------------------------------------------
# JWT token management
# ----------------------------------------------------------------
TokenType = Literal["access", "refresh"]


def create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT token.

    Args:
        subject: The user identifier (user ID as string)
        token_type: "access" or "refresh"
        expires_delta: Custom expiry, defaults to settings value

    The token contains:
        sub: subject (user ID)
        type: token type (access/refresh)
        iat: issued at timestamp
        exp: expiry timestamp
    """
    now = datetime.now(timezone.utc)

    if expires_delta is None:
        if token_type == "access":
            expires_delta = timedelta(
                minutes=settings.jwt_access_token_expire_minutes
            )
        else:
            expires_delta = timedelta(days=7)  # Refresh tokens live longer

    expire = now + expires_delta

    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": expire,
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    logger.debug(
        "jwt_token_created",
        token_type=token_type,
        subject=subject,
        expires_at=expire.isoformat(),
    )

    return token


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Raises JWTError if:
    - Token signature is invalid (tampered)
    - Token has expired
    - Token is malformed

    Never catches JWTError here — let the caller decide
    how to handle invalid tokens (usually return 401).
    """
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def create_token_pair(user_id: str) -> dict:
    """
    Create both access and refresh tokens for a user.
    Called after successful authentication.
    Returns a dict ready to send as the login response.
    """
    access_token = create_token(
        subject=user_id,
        token_type="access",
    )
    refresh_token = create_token(
        subject=user_id,
        token_type="refresh",
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_token_expire_minutes * 60,
    }
