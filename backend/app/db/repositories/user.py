"""
User repository — data access layer for authentication.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.user import User

logger = get_logger(__name__)


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        email: str,
        username: str,
        hashed_password: str,
    ) -> User:
        """Create a new user with a pre-hashed password."""
        user = User(
            email=email.lower().strip(),
            username=username.lower().strip(),
            hashed_password=hashed_password,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        logger.info("user_created", user_id=str(user.id), email=user.email)
        return user

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        import uuid
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return None
        result = await self.session.execute(
            select(User).where(User.id == uid)
        )
        return result.scalar_one_or_none()

    async def record_login(self, user: User) -> None:
        """Update last login timestamp and reset failed attempts."""
        user.last_login_at = datetime.now(timezone.utc)
        user.failed_login_attempts = 0
        await self.session.flush()

    async def increment_failed_login(self, user: User) -> None:
        """Track failed login attempts for lockout logic."""
        user.failed_login_attempts += 1
        await self.session.flush()
        logger.warning(
            "failed_login_attempt",
            user_id=str(user.id),
            attempts=user.failed_login_attempts,
        )
