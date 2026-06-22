"""
FastAPI dependencies for authentication and authorization.

These functions are injected into route handlers via Depends().
They extract and validate the JWT token from every request
before the route handler runs.

Usage in any route:
    @router.get("/protected")
    async def protected_route(
        current_user: User = Depends(get_current_user)
    ):
        ...

That single line makes the route require a valid JWT.
No auth = 401 Unauthorized automatically.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import decode_token
from app.db.engine import get_db_session
from app.db.models.user import User
from app.db.repositories.user import UserRepository

logger = get_logger(__name__)

# HTTPBearer extracts the token from Authorization: Bearer <token> header
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Extracts and validates the JWT from the Authorization header.
    Returns the authenticated User object.
    Raises 401 if token is missing, invalid, or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    try:
        payload = decode_token(credentials.credentials)

        # Verify this is an access token, not a refresh token
        if payload.get("type") != "access":
            raise credentials_exception

        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception

    except JWTError:
        logger.warning("jwt_validation_failed")
        raise credentials_exception

    # Load user from database
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)

    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    return user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Requires the authenticated user to be a superuser.
    Use for admin-only endpoints.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user
