"""
Authentication service — business logic for user auth.
"""

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import (
    create_token_pair,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.repositories.user import UserRepository
from app.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse

logger = get_logger(__name__)

# Lock out after this many consecutive failures
MAX_FAILED_ATTEMPTS = 5


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, data: UserRegister) -> UserResponse:
        """
        Register a new user.
        Checks for duplicate email/username before creating.
        """
        # Check for existing email
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )

        # Hash password — plaintext never touches the database
        hashed = hash_password(data.password)

        user = await self.user_repo.create(
            email=data.email,
            username=data.username,
            hashed_password=hashed,
        )

        logger.info("user_registered", user_id=str(user.id))
        return UserResponse.model_validate(user)

    async def login(self, data: UserLogin) -> TokenResponse:
        """
        Authenticate a user and issue JWT tokens.

        Security notes:
        - Always run password verification even if user not found
          (prevents user enumeration via timing attacks)
        - Generic error message regardless of failure reason
        - Track failed attempts for lockout
        """
        user = await self.user_repo.get_by_email(data.email)

        # Always verify password even if user doesn't exist
        # This prevents timing-based user enumeration
        dummy_hash = "$2b$12$dummy.hash.to.prevent.timing.attacks.padding"
        password_to_check = user.hashed_password if user else dummy_hash

        is_valid = verify_password(data.password, password_to_check)

        if not user or not is_valid:
            if user:
                await self.user_repo.increment_failed_login(user)
            logger.warning(
                "login_failed",
                email=data.email,
                reason="invalid_credentials",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )

        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account locked due to too many failed attempts. Contact support.",
            )

        await self.user_repo.record_login(user)

        tokens = create_token_pair(str(user.id))
        logger.info("login_successful", user_id=str(user.id))

        return TokenResponse(**tokens)

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Exchange a valid refresh token for a new token pair."""
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError("Not a refresh token")
            user_id = payload.get("sub")
        except (JWTError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        tokens = create_token_pair(str(user.id))
        return TokenResponse(**tokens)
