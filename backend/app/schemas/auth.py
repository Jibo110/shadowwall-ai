"""
Authentication request/response schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    """Schema for creating a new user account."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        """
        Enforce basic password strength.
        In production this would be more sophisticated.
        """
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one digit")
        return value

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, value: str) -> str:
        """Prevent username injection attacks."""
        if not value.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores and hyphens allowed)")
        return value.lower()


class UserLogin(BaseModel):
    """Schema for login requests."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for successful auth responses."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """Public user data — never includes password hash."""
    id: uuid.UUID
    email: str
    username: str
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RefreshRequest(BaseModel):
    """Schema for token refresh requests."""
    refresh_token: str
