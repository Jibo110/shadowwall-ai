"""
HoneyToken API routes.

This module only handles HTTP concerns:
  - Defining endpoints (method + path)
  - Declaring request/response schemas
  - Injecting dependencies (db session, rate limiter)
  - Calling the service layer
  - Returning responses

It contains ZERO business logic and ZERO database queries.
All of that lives in the service and repository layers.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.engine import get_db_session
from app.db.models.token import TokenStatus
from app.schemas.token import (
    TokenCreate,
    TokenListResponse,
    TokenResponse,
    TokenUpdate,
)
from app.services.token import TokenService

logger = get_logger(__name__)

# APIRouter groups related endpoints together.
# The prefix and tags are applied to every route in this file.
router = APIRouter(
    prefix="/tokens",
    tags=["Honey Tokens"],
)


# ----------------------------------------------------------------
# Dependency: Token Service
# FastAPI calls this function and injects the result into routes
# that declare `service: TokenService = Depends(get_token_service)`
# ----------------------------------------------------------------
async def get_token_service(
    session: AsyncSession = Depends(get_db_session),
) -> TokenService:
    """Constructs a TokenService with a database session."""
    return TokenService(session)


# ----------------------------------------------------------------
# POST /tokens
# Create a new honey token
# ----------------------------------------------------------------
@router.post(
    "/",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Deploy a new honey token",
    description=(
        "Creates and deploys a new honey token. "
        "The token value is stored securely and monitored for unauthorized access."
    ),
)
async def create_token(
    payload: TokenCreate,
    service: TokenService = Depends(get_token_service),
) -> TokenResponse:
    logger.info("api_create_token", label=payload.label, token_type=payload.token_type)
    return await service.create_token(payload)


# ----------------------------------------------------------------
# GET /tokens
# List all tokens with pagination and optional filtering
# ----------------------------------------------------------------
@router.get(
    "/",
    response_model=TokenListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all honey tokens",
)
async def list_tokens(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: TokenStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by token status",
    ),
    service: TokenService = Depends(get_token_service),
) -> TokenListResponse:
    return await service.list_tokens(
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )


# ----------------------------------------------------------------
# GET /tokens/{token_id}
# Retrieve a single token by ID
# ----------------------------------------------------------------
@router.get(
    "/{token_id}",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a honey token by ID",
)
async def get_token(
    token_id: uuid.UUID,
    service: TokenService = Depends(get_token_service),
) -> TokenResponse:
    return await service.get_token(token_id)


# ----------------------------------------------------------------
# PATCH /tokens/{token_id}
# Partially update a token
# ----------------------------------------------------------------
@router.patch(
    "/{token_id}",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a honey token",
)
async def update_token(
    token_id: uuid.UUID,
    payload: TokenUpdate,
    service: TokenService = Depends(get_token_service),
) -> TokenResponse:
    return await service.update_token(token_id, payload)


# ----------------------------------------------------------------
# DELETE /tokens/{token_id}
# ----------------------------------------------------------------
@router.delete(
    "/{token_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a honey token",
)
async def delete_token(
    token_id: uuid.UUID,
    service: TokenService = Depends(get_token_service),
) -> dict:
    return await service.delete_token(token_id)
