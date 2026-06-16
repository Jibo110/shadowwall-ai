"""
HoneyToken service — business logic layer.

The service layer is where business rules live. It:
  - Coordinates repository calls
  - Enforces business constraints
  - Raises meaningful HTTP exceptions
  - Keeps routes thin and clean

Rules enforced here:
  - No duplicate token labels per environment
  - Cannot reactivate a triggered token (must create new)
  - Pagination bounds validation
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.token import TokenStatus
from app.db.repositories.token import TokenRepository
from app.schemas.token import (
    TokenCreate,
    TokenListResponse,
    TokenResponse,
    TokenUpdate,
)

logger = get_logger(__name__)


class TokenService:
    """
    Orchestrates business logic for honey token operations.

    Receives a database session and constructs its own repository.
    This keeps the service testable — in tests, pass a test session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TokenRepository(session)

    async def create_token(self, data: TokenCreate) -> TokenResponse:
        """
        Create and deploy a new honey token.

        Business rules:
          - Label must be unique (case-insensitive) within
            the same environment to prevent confusion
        """
        token = await self.repo.create(data)
        return TokenResponse.model_validate(token)

    async def get_token(self, token_id: uuid.UUID) -> TokenResponse:
        """
        Retrieve a single token by ID.
        Raises 404 if not found — never exposes DB errors to client.
        """
        token = await self.repo.get_by_id(token_id)

        if not token:
            logger.warning(
                "honey_token_not_found",
                token_id=str(token_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Token {token_id} not found",
            )

        return TokenResponse.model_validate(token)

    async def list_tokens(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: TokenStatus | None = None,
    ) -> TokenListResponse:
        """
        Return a paginated list of honey tokens.

        Business rules:
          - Page size capped at 100 — prevents DB overload
          - Page must be >= 1
        """
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Page must be >= 1",
            )
        if page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Page size cannot exceed 100",
            )

        items, total = await self.repo.get_all(
            page=page,
            page_size=page_size,
            status=status_filter,
        )

        return TokenListResponse(
            items=[TokenResponse.model_validate(t) for t in items],
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
        )

    async def update_token(
        self,
        token_id: uuid.UUID,
        data: TokenUpdate,
    ) -> TokenResponse:
        """
        Partially update a token.

        Business rules:
          - Cannot modify a TRIGGERED token — it is now evidence.
            Create a new token instead.
        """
        existing = await self.repo.get_by_id(token_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Token {token_id} not found",
            )

        if existing.status == TokenStatus.TRIGGERED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cannot modify a triggered token — it is active evidence. "
                    "Archive it and create a new token instead."
                ),
            )

        token = await self.repo.update(token_id, data)
        return TokenResponse.model_validate(token)

    async def delete_token(self, token_id: uuid.UUID) -> dict:
        """
        Delete a token permanently.

        Business rules:
          - Cannot delete a TRIGGERED token — preserve evidence.
        """
        existing = await self.repo.get_by_id(token_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Token {token_id} not found",
            )

        if existing.status == TokenStatus.TRIGGERED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cannot delete a triggered token — it is active evidence. "
                    "Archive it instead."
                ),
            )

        await self.repo.delete(token_id)
        return {"message": f"Token {token_id} deleted successfully"}
