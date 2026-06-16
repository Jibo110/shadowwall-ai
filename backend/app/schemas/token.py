"""
Pydantic schemas for HoneyToken API contracts.

Schemas serve three purposes:
1. Input validation  — reject malformed requests before they reach business logic
2. Output shaping    — control exactly what fields the API exposes
3. Documentation     — FastAPI reads these to generate Swagger UI automatically

We use separate schemas for different operations (Create, Update, Response)
rather than one schema for everything. This gives us precise control over
what fields are required, optional, or read-only at each stage.

Pattern:
    TokenBase       → shared fields
    TokenCreate     → fields required to create (input)
    TokenUpdate     → fields allowed to update (all optional)
    TokenResponse   → fields returned to client (output)
    TokenListResponse → paginated list wrapper
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.db.models.token import TokenStatus, TokenType


# ----------------------------------------------------------------
# Base Schema
# Contains fields shared across multiple schemas.
# Never used directly in routes — only inherited.
# ----------------------------------------------------------------
class TokenBase(BaseModel):
    label: str = Field(
        min_length=1,
        max_length=255,
        description="Human-readable name for this token",
        examples=["Production AWS Key"],
    )
    token_type: TokenType = Field(
        description="Category of honey token",
        examples=[TokenType.API_KEY],
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Where this token was planted and why",
        examples=["Planted in the .env file of the staging server"],
    )
    environment: str | None = Field(
        default=None,
        max_length=100,
        description="Environment where the token is deployed",
        examples=["production"],
    )
    planted_location: str | None = Field(
        default=None,
        max_length=500,
        description="Specific location where token was planted",
        examples=[".env file, GitHub Actions secrets"],
    )


# ----------------------------------------------------------------
# Create Schema
# Defines what a client must send to create a new token.
# token_value is required here but never returned in responses.
# ----------------------------------------------------------------
class TokenCreate(TokenBase):
    token_value: str = Field(
        min_length=8,
        max_length=5000,
        description="The fake secret value to plant",
        examples=["AKIAIOSFODNN7EXAMPLE"],
    )

    @field_validator("token_value")
    @classmethod
    def token_value_not_real(cls, value: str) -> str:
        """
        Basic guard against accidentally planting real secrets.
        Rejects values that look like real OpenAI or AWS keys.

        In production this would be more sophisticated —
        checking against known secret formats with regex.
        """
        real_key_indicators = [
            "sk-proj-",   # Real OpenAI project key
            "sk-ant-",    # Real Anthropic key
        ]
        for indicator in real_key_indicators:
            if value.startswith(indicator):
                raise ValueError(
                    "Token value appears to be a real secret. "
                    "Use a fake/decoy value instead."
                )
        return value


# ----------------------------------------------------------------
# Update Schema
# All fields optional — client sends only what they want to change.
# This is the PATCH pattern (partial update).
# ----------------------------------------------------------------
class TokenUpdate(BaseModel):
    label: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
    )
    environment: str | None = Field(
        default=None,
        max_length=100,
    )
    planted_location: str | None = Field(
        default=None,
        max_length=500,
    )
    status: TokenStatus | None = None
    is_active: bool | None = None


# ----------------------------------------------------------------
# Response Schema
# Defines what the API returns to the client.
# Notice: token_value is NOT here — we never return the fake
# secret in list/detail responses (reduces exposure).
# ----------------------------------------------------------------
class TokenResponse(TokenBase):
    id: uuid.UUID
    status: TokenStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    triggered_at: datetime | None

    # model_config tells Pydantic to read data from ORM objects
    # (SQLAlchemy models) not just plain dictionaries.
    model_config = {"from_attributes": True}


# ----------------------------------------------------------------
# List Response Schema
# Wraps a list of tokens with pagination metadata.
# Always paginate list endpoints — never return unbounded lists.
# ----------------------------------------------------------------
class TokenListResponse(BaseModel):
    items: list[TokenResponse]
    total: int
    page: int
    page_size: int
    has_next: bool

    model_config = {"from_attributes": True}
