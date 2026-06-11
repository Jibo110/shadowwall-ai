"""
HoneyToken database model.

A HoneyToken is a deliberately planted fake credential, API key,
database record, or file — designed to look legitimate but serve
no real operational purpose. Any interaction with a honey token
is an unambiguous indicator of compromise (IoC).

This model stores the token definition and its metadata.
Trigger events (when the token is accessed) are stored separately
in the TriggerEvent model (Day 4).
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.engine import Base


class TokenType(str, enum.Enum):
    """
    Categories of honey tokens we can deploy.

    Using str + enum.Enum means the value is stored as a string
    in PostgreSQL and serializes cleanly to JSON in API responses.
    """
    API_KEY = "api_key"           # Fake API credentials
    DATABASE_URL = "database_url" # Fake connection string
    AWS_KEY = "aws_key"           # Fake AWS access key
    JWT_SECRET = "jwt_secret"     # Fake signing secret
    SSH_KEY = "ssh_key"           # Fake private key
    WEBHOOK_URL = "webhook_url"   # Fake webhook endpoint
    CUSTOM = "custom"             # User-defined token type


class TokenStatus(str, enum.Enum):
    """Lifecycle state of a honey token."""
    ACTIVE = "active"       # Deployed and monitoring
    TRIGGERED = "triggered" # Has been accessed — incident in progress
    EXPIRED = "expired"     # Manually deactivated
    ARCHIVED = "archived"   # Removed from active monitoring


class HoneyToken(Base):
    """
    Represents a single deployed honey token.

    Design decisions:
    - UUID primary key: prevents enumeration attacks (vs integer IDs)
    - created_at/updated_at: audit trail for compliance
    - token_value is the fake secret — stored here so we can
      recognize it if it appears in a request
    - label is human-readable name for the dashboard
    - description explains where it was planted (for the analyst)
    """

    __tablename__ = "honey_tokens"

    # ----------------------------------------------------------------
    # Primary Key
    # UUID prevents attackers from guessing/enumerating IDs.
    # server_default generates the UUID in PostgreSQL itself.
    # ----------------------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ----------------------------------------------------------------
    # Token Identity
    # ----------------------------------------------------------------
    label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable name shown on dashboard",
    )

    token_type: Mapped[TokenType] = mapped_column(
        Enum(TokenType, name="token_type_enum"),
        nullable=False,
        index=True,
    )

    token_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The fake secret value planted in the environment",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Where this token was planted and why",
    )

    # ----------------------------------------------------------------
    # Deployment Context
    # Where was this token planted? Used by the AI agent for context.
    # ----------------------------------------------------------------
    environment: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="e.g. production, staging, ci-cd",
    )

    planted_location: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="e.g. .env file, GitHub repo, S3 bucket",
    )

    # ----------------------------------------------------------------
    # Status
    # ----------------------------------------------------------------
    status: Mapped[TokenStatus] = mapped_column(
        Enum(TokenStatus, name="token_status_enum"),
        nullable=False,
        default=TokenStatus.ACTIVE,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # ----------------------------------------------------------------
    # Audit Timestamps
    # All times stored in UTC — never local time.
    # ----------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of first trigger event",
    )

    def __repr__(self) -> str:
        return (
            f"HoneyToken(id={self.id!r}, "
            f"label={self.label!r}, "
            f"type={self.token_type!r}, "
            f"status={self.status!r})"
        )
