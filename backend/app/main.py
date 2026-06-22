"""
ShadowWall AI — FastAPI Application Entry Point

This module bootstraps the entire backend application:
- Configures structured logging
- Creates the FastAPI app with security middleware
- Registers CORS, rate limiting, and metrics middleware
- Mounts API routers
- Defines startup and shutdown lifecycle hooks

Architecture note:
    We use the lifespan context manager pattern (not deprecated
    @app.on_event) for startup/shutdown — this is the modern
    FastAPI standard as of v0.93+
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from app.db.engine import close_db, init_db
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.api.v1.router import api_router

from app.core.middleware import SecurityHeadersMiddleware
# ----------------------------------------------------------------
# Bootstrap logging FIRST — before anything else.
# If logging fails, we want to know immediately.
# ----------------------------------------------------------------
setup_logging()
logger = get_logger(__name__)
settings = get_settings()


# ----------------------------------------------------------------
# Rate Limiter
# Initialized here so it can be imported by route modules.
# get_remote_address extracts the real client IP from the request.
# ----------------------------------------------------------------
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)


# ----------------------------------------------------------------
# Application Lifespan
# Handles startup and shutdown logic cleanly.
# ----------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages application startup and shutdown.

    Everything BEFORE yield runs at startup.
    Everything AFTER yield runs at shutdown.

    This is where we will later:
    - Initialize the database connection pool
    - Connect to Redis
    - Warm up the LangGraph agent
    """
    # --- STARTUP ---
    logger.info(
        "shadowwall_ai_starting",
        environment=settings.app_env,
        debug=settings.app_debug,
        version="0.1.0",
    )

    # Placeholder: database pool init comes in Day 3
    # Placeholder: Redis connection comes in Day 3

   # Verify database connectivity
    await init_db()

    logger.info("shadowwall_ai_ready")

    yield  # Application runs here

    # --- SHUTDOWN ---
    logger.info("shadowwall_ai_shutting_down")

    # Close database connection pool gracefully
    await close_db()

    # Placeholder: close database pool
    # Placeholder: close Redis connection


# ----------------------------------------------------------------
# FastAPI Application Instance
# ----------------------------------------------------------------
app = FastAPI(
    title="ShadowWall AI",
    description="Real-time cyber deception dashboard with autonomous AI threat response",
    version="0.1.0",
    # Disable docs in production — never expose API schema publicly
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
    lifespan=lifespan,
)


# ----------------------------------------------------------------
# Middleware Stack
# Order matters — middleware executes in reverse registration order.
# ----------------------------------------------------------------

# 0. Security Headers — must be first
# app.add_middleware(SecurityHeadersMiddleware)


# 1. Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 2. CORS — Cross Origin Resource Sharing
# Controls which frontend origins can talk to this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.allowed_origins],
    allow_credentials=True,
    # In production this should be a specific list, not wildcard
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


# ----------------------------------------------------------------
# Health Check Endpoint
# Used by Docker, load balancers, and monitoring tools to verify
# the service is alive. No auth required. No sensitive data exposed.
# ----------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """
    Returns service health status.

    This endpoint is intentionally minimal — it confirms the
    application process is running and responding to requests.
    Deep health checks (database, Redis) will be added separately.
    """
    return {
        "status": "healthy",
        "service": "shadowwall-ai",
        "version": "0.1.0",
        "environment": settings.app_env,
    }

# Mount all API routes under /api/v1
app.include_router(api_router)
# ----------------------------------------------------------------
# Root endpoint
# ----------------------------------------------------------------
@app.get("/", tags=["System"])
async def root() -> dict:
    """API root — confirms the service is reachable."""
    return {
        "message": "ShadowWall AI API",
        "docs": "/docs" if settings.is_development else "disabled in production",
    }
