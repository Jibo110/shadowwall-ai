"""
API v1 router aggregator.
"""

from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.events import router as events_router
from app.api.v1.routes.tokens import router as tokens_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(tokens_router)
api_router.include_router(events_router)
