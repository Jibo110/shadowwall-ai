"""
User database model.

Stores authenticated users who can access the ShadowWall AI dashboard.
Passwords are NEVER stored in plain text — only bcrypt hashes.

Security design decisions:
- UUID primary key: prevents enumeration attacks
- is_active flag: disable accounts without deleting audit trail
- is_superuser flag: role-based access foundation
- last_login_at: audit trail for security reviews
- failed_login_attempts: brute force detection foundation
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.engine import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ----------------------------------------------------------------
    # Identity
    # ----------------------------------------------------------------
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Primary identifier — used for login",
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    # ----------------------------------------------------------------
    # Security — hashed password only, never plaintext
    # ----------------------------------------------------------------
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt hash — never store plaintext",
    )

    # ----------------------------------------------------------------
    # Access control
    # ----------------------------------------------------------------
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Disabled accounts cannot log in",
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Superusers can manage other users",
    )

    # ----------------------------------------------------------------
    # Audit fields
    # ----------------------------------------------------------------
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Consecutive failed logins — used for lockout",
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

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

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r}, active={self.is_active!r})"
