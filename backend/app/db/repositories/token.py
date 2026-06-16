"""
HoneyToken repository — data access layer.

This module is the ONLY place in the codebase that directly
queries the database for honey tokens. All database operations
are isolated here.

Why repositories?
    - Routes and services stay clean — no SQL scattered everywhere
    - Easy to test — inject a mock repository in unit tests
    - Easy to swap databases — change one file, not fifty
    - Consistent error handling in one place

All methods are async — they never block the event loop.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.token import HoneyToken, TokenStatus
from app.schemas.token import TokenCreate, TokenUpdate

logger = get_logger(__name__)


class TokenRepository:
    """
    Handles all database operations for HoneyToken records.

    Receives an AsyncSession via dependency injection —
    never creates its own database connections.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: TokenCreate) -> HoneyToken:
        """
        Persist a new honey token to the database.

        The session commit happens in the get_db_session dependency
        (engine.py) — not here. The repository only flushes to get
        the generated ID back without committing the transaction.
        This allows the service layer to coordinate multiple
        repository calls in a single atomic transaction.
        """
        token = HoneyToken(
            label=data.label,
            token_type=data.token_type,
            token_value=data.token_value,
            description=data.description,
            environment=data.environment,
            planted_location=data.planted_location,
        )
        self.session.add(token)
        # flush = send SQL to DB but don't commit yet
        # This gives us the generated UUID back
        await self.session.flush()
        await self.session.refresh(token)

        logger.info(
            "honey_token_created",
            token_id=str(token.id),
            token_type=token.token_type,
            label=token.label,
        )
        return token

    async def get_by_id(self, token_id: uuid.UUID) -> HoneyToken | None:
        """
        Fetch a single token by its UUID.
        Returns None if not found — the service layer decides
        whether to raise a 404 or handle it differently.
        """
        result = await self.session.execute(
            select(HoneyToken).where(HoneyToken.id == token_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        status: TokenStatus | None = None,
    ) -> tuple[list[HoneyToken], int]:
        """
        Fetch a paginated list of tokens with optional status filter.

        Returns a tuple of (items, total_count).
        We fetch the count and items in separate queries for clarity.
        In high-scale systems this could be optimized with a window
        function, but clarity wins at this stage.
        """
        # Base query — filter by status if provided
        base_query = select(HoneyToken)
        count_query = select(func.count()).select_from(HoneyToken)

        if status is not None:
            base_query = base_query.where(HoneyToken.status == status)
            count_query = count_query.where(HoneyToken.status == status)

        # Get total count for pagination metadata
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        offset = (page - 1) * page_size
        items_result = await self.session.execute(
            base_query
            .order_by(HoneyToken.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(items_result.scalars().all())

        return items, total

    async def update(
        self,
        token_id: uuid.UUID,
        data: TokenUpdate,
    ) -> HoneyToken | None:
        """
        Partially update a token (PATCH semantics).
        Only updates fields that are explicitly provided.
        Fields set to None in the schema are left unchanged.
        """
        # Build dict of only the fields that were actually provided
        update_data = data.model_dump(exclude_none=True)

        if not update_data:
            # Nothing to update — fetch and return current state
            return await self.get_by_id(token_id)

        update_data["updated_at"] = datetime.now(timezone.utc)

        await self.session.execute(
            update(HoneyToken)
            .where(HoneyToken.id == token_id)
            .values(**update_data)
        )
        await self.session.flush()
        return await self.get_by_id(token_id)

    async def mark_triggered(self, token_id: uuid.UUID) -> HoneyToken | None:
        """
        Mark a token as triggered — called by the AI agent
        when it detects unauthorized access to a honey token.
        Sets status to TRIGGERED and records the trigger timestamp.
        """
        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(HoneyToken)
            .where(HoneyToken.id == token_id)
            .values(
                status=TokenStatus.TRIGGERED,
                triggered_at=now,
                updated_at=now,
            )
        )
        await self.session.flush()
        token = await self.get_by_id(token_id)

        if token:
            logger.warning(
                "honey_token_triggered",
                token_id=str(token_id),
                triggered_at=now.isoformat(),
            )
        return token

    async def delete(self, token_id: uuid.UUID) -> bool:
        """
        Hard delete a token by ID.
        Returns True if deleted, False if not found.

        Note: In production security systems you often want
        soft deletes (setting is_active=False) to preserve
        audit trails. We offer both patterns here.
        """
        token = await self.get_by_id(token_id)
        if not token:
            return False
        await self.session.delete(token)
        await self.session.flush()

        logger.info("honey_token_deleted", token_id=str(token_id))
        return True
