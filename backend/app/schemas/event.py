"""
Pydantic schemas for TriggerEvent API contracts.

A TriggerEvent is created whenever a honey token is accessed.
It captures the full context of the access attempt:
who, what, when, where, and how.
"""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    """
    AI-assessed severity of a trigger event.
    Set by the LangGraph agent after analysis.
    """
    LOW = "low"           # Likely automated scanner
    MEDIUM = "medium"     # Suspicious but unclear intent
    HIGH = "high"         # Targeted access, likely human
    CRITICAL = "critical" # Confirmed breach indicator


class TriggerEventCreate(BaseModel):
    """Data required to record a new trigger event."""
    token_id: uuid.UUID = Field(description="ID of the triggered honey token")
    source_ip: str = Field(
        max_length=45,
        description="IP address of the accessor (supports IPv6)",
        examples=["192.168.1.100"],
    )
    user_agent: str | None = Field(
        default=None,
        max_length=500,
        description="HTTP User-Agent string from the request",
    )
    request_method: str | None = Field(
        default=None,
        max_length=10,
        description="HTTP method used",
        examples=["GET", "POST"],
    )
    request_path: str | None = Field(
        default=None,
        max_length=2000,
        description="URL path that was accessed",
    )
    additional_context: dict | None = Field(
        default=None,
        description="Any extra metadata captured at trigger time",
    )


class TriggerEventResponse(BaseModel):
    """Full event data returned by the API."""
    id: uuid.UUID
    token_id: uuid.UUID
    source_ip: str
    user_agent: str | None
    request_method: str | None
    request_path: str | None
    severity: SeverityLevel
    agent_analysis: str | None
    additional_context: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WebSocketEvent(BaseModel):
    """
    Structure of every message sent over WebSocket.

    Every real-time message has a consistent envelope:
    - type: what kind of event this is
    - payload: the actual event data
    - timestamp: when it was emitted

    This consistency means the frontend can switch on 'type'
    and handle different events with a clean dispatch pattern.
    """
    type: str
    payload: dict
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now()
    )

    model_config = {"from_attributes": True}
