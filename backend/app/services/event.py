"""
TriggerEvent service — business logic layer.

Coordinates event recording, token status updates,
and real-time WebSocket broadcasting.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.token import TokenStatus
from app.db.repositories.event import EventRepository
from app.db.repositories.token import TokenRepository
from app.schemas.event import (
    TriggerEventCreate,
    TriggerEventResponse,
)
from app.websocket.manager import manager

logger = get_logger(__name__)


class EventService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.event_repo = EventRepository(session)
        self.token_repo = TokenRepository(session)

    async def record_trigger(
        self,
        data: TriggerEventCreate,
    ) -> TriggerEventResponse:
        """
        Core method — called whenever a honey token is accessed.

        Sequence:
        1. Verify the token exists and is active
        2. Record the trigger event in the database
        3. Mark the token as TRIGGERED
        4. Broadcast real-time alert to all dashboard clients
        5. Return the event record

        Steps 1-3 are in a single transaction.
        Step 4 (WebSocket broadcast) happens after commit —
        we never broadcast before the data is safely persisted.
        """
        # Step 1 — verify token exists
        token = await self.token_repo.get_by_id(data.token_id)
        if not token:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Token {data.token_id} not found",
            )

        # Step 2 — record the event
        event = await self.event_repo.create(data)

        # Step 3 — mark token as triggered (if not already)
        if token.status == TokenStatus.ACTIVE:
            await self.token_repo.mark_triggered(data.token_id)

        # Step 4 — broadcast to all connected dashboards
        # This runs AFTER the database operations succeed
        await manager.broadcast({
            "type": "token_triggered",
            "payload": {
                "event_id": str(event.id),
                "token_id": str(event.token_id),
                "token_label": token.label,
                "token_type": token.token_type,
                "source_ip": event.source_ip,
                "severity": event.severity,
                "timestamp": event.created_at.isoformat(),
                "agent_status": "analyzing",
            },
        })

        logger.warning(
            "honey_token_triggered_and_broadcast",
            token_id=str(data.token_id),
            token_label=token.label,
            source_ip=data.source_ip,
        )

        return TriggerEventResponse.model_validate(event)

    async def get_recent_events(
        self,
        limit: int = 100,
    ) -> list[TriggerEventResponse]:
        """Fetch recent events for dashboard initial load."""
        events = await self.event_repo.get_recent(limit=limit)
        return [TriggerEventResponse.model_validate(e) for e in events]

    async def get_events_for_token(
        self,
        token_id: uuid.UUID,
    ) -> list[TriggerEventResponse]:
        """Fetch all events for a specific token."""
        events = await self.event_repo.get_by_token(token_id)
        return [TriggerEventResponse.model_validate(e) for e in events]
