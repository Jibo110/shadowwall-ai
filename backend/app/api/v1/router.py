"""
API v1 router aggregator.

All route modules for version 1 of the API are registered here.
This file is the single place to add new route groups as the
application grows.

To add a new resource:
    1. Create app/api/v1/routes/your_resource.py
    2. Import its router here
    3. Add: api_router.include_router(your_router)
"""

from fastapi import APIRouter

from app.api.v1.routes.tokens import router as tokens_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(tokens_router)
