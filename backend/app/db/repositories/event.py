"""
TriggerEvent repository — data access layer.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.db.models.event import TriggerEvent
from app.schemas.event import SeverityLevel, TriggerEventCreate

logger = get_logger(__name__)


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: TriggerEventCreate) -> TriggerEvent:
        """Record a new trigger event."""
        event = TriggerEvent(
            token_id=data.token_id,
            source_ip=data.source_ip,
            user_agent=data.user_agent,
            request_method=data.request_method,
            request_path=data.request_path,
            additional_context=data.additional_context,
            severity=SeverityLevel.MEDIUM,  # AI agent updates this later
        )
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)

        logger.warning(
            "trigger_event_recorded",
            event_id=str(event.id),
            token_id=str(event.token_id),
            source_ip=event.source_ip,
            severity=event.severity,
        )
        return event

    async def get_by_token(
        self,
        token_id: uuid.UUID,
        limit: int = 50,
    ) -> list[TriggerEvent]:
        """Fetch all events for a specific token, newest first."""
        result = await self.session.execute(
            select(TriggerEvent)
            .where(TriggerEvent.token_id == token_id)
            .order_by(TriggerEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(self, limit: int = 100) -> list[TriggerEvent]:
        """
        Fetch the most recent events across all tokens.
        Used by the dashboard to populate the live feed.
        """
        result = await self.session.execute(
            select(TriggerEvent)
            .options(selectinload(TriggerEvent.token))
            .order_by(TriggerEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_agent_analysis(
        self,
        event_id: uuid.UUID,
        severity: SeverityLevel,
        analysis: str,
    ) -> TriggerEvent | None:
        """
        Called by the LangGraph agent after it finishes analysis.
        Updates severity and writes the natural language report.
        """
        from sqlalchemy import update
        await self.session.execute(
            update(TriggerEvent)
            .where(TriggerEvent.id == event_id)
            .values(severity=severity, agent_analysis=analysis)
        )
        await self.session.flush()
        result = await self.session.execute(
            select(TriggerEvent).where(TriggerEvent.id == event_id)
        )
        return result.scalar_one_or_none()
