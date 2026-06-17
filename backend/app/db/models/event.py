"""
TriggerEvent database model.

A TriggerEvent is recorded every time a honey token is accessed.
This is the core forensic record — it captures everything we know
about the access attempt at the moment it happened.

The AI agent later enriches this record with:
- Severity assessment
- Threat classification
- Natural language analysis
- Recommended response actions
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.engine import Base
from app.schemas.event import SeverityLevel


class TriggerEvent(Base):
    """
    Records every unauthorized access to a honey token.

    Design decisions:
    - JSONB for additional_context: flexible schema for varied
      metadata without requiring schema migrations for new fields
    - ForeignKey to honey_tokens: events are always linked to
      the token that was triggered
    - agent_analysis stored as Text: the LangGraph agent writes
      its natural language analysis directly to this field
    """

    __tablename__ = "trigger_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ----------------------------------------------------------------
    # Foreign Key — which token was triggered
    # ----------------------------------------------------------------
    token_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("honey_tokens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The honey token that was accessed",
    )

    # ----------------------------------------------------------------
    # Access Context — forensic data about the access attempt
    # ----------------------------------------------------------------
    source_ip: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
        index=True,
        comment="IP address of accessor (IPv4 or IPv6)",
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="HTTP User-Agent header from the request",
    )

    request_method: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="HTTP method: GET, POST, etc.",
    )

    request_path: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        comment="URL path that was accessed",
    )

    additional_context: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Flexible metadata — headers, geo data, etc.",
    )

    # ----------------------------------------------------------------
    # AI Agent Assessment
    # Populated asynchronously after the LangGraph agent runs
    # ----------------------------------------------------------------
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SeverityLevel.MEDIUM,
        comment="AI-assessed severity: low, medium, high, critical",
    )

    agent_analysis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Natural language analysis from LangGraph agent",
    )

    # ----------------------------------------------------------------
    # Timestamp
    # ----------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ----------------------------------------------------------------
    # Relationship — access the parent token from an event
    # ----------------------------------------------------------------
    token: Mapped["HoneyToken"] = relationship(  # type: ignore[name-defined]
        "HoneyToken",
        back_populates="events",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"TriggerEvent(id={self.id!r}, "
            f"token_id={self.token_id!r}, "
            f"source_ip={self.source_ip!r}, "
            f"severity={self.severity!r})"
        )
