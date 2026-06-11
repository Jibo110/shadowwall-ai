"""
Database engine and session management.

We use SQLAlchemy 2.0 with async support via asyncpg driver.
This module provides:
  - The async engine (connection pool to PostgreSQL)
  - The async session factory (for database transactions)
  - A dependency-injectable session for FastAPI routes

Architecture note:
    We never import 'engine' or 'AsyncSession' directly in routes.
    Routes receive a session via FastAPI's Depends() injection.
    This keeps routes clean and makes testing trivial — tests can
    inject a test session without touching real database code.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ----------------------------------------------------------------
# Async Engine
# The engine manages the connection pool to PostgreSQL.
# pool_size = number of persistent connections kept open
# max_overflow = extra connections allowed under heavy load
# pool_pre_ping = test connections before using them
#                 (prevents "connection closed" errors after idle)
# echo = log every SQL statement (True in dev for visibility)
# ----------------------------------------------------------------
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    echo=settings.is_development,
    future=True,
)


# ----------------------------------------------------------------
# Session Factory
# Creates individual database sessions (transactions).
# expire_on_commit=False means objects remain accessible
# after a commit — important for async patterns.
# ----------------------------------------------------------------
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ----------------------------------------------------------------
# Declarative Base
# All SQLAlchemy ORM models inherit from this class.
# It maintains a registry of all models — Alembic uses this
# registry to detect schema changes and generate migrations.
# ----------------------------------------------------------------
class Base(DeclarativeBase):
    """
    Base class for all database models.

    Every model in app/db/models/ inherits from this.
    Example:
        from app.db.engine import Base
        class HoneyToken(Base):
            __tablename__ = "honey_tokens"
            ...
    """
    pass


# ----------------------------------------------------------------
# FastAPI Dependency
# Injected into routes via Depends(get_db_session).
# Opens a session, yields it to the route handler,
# then automatically commits or rolls back and closes.
# ----------------------------------------------------------------
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a database session for a single request lifecycle.

    Usage in a FastAPI route:
        from app.db.engine import get_db_session
        from sqlalchemy.ext.asyncio import AsyncSession
        from fastapi import Depends

        @router.get("/tokens")
        async def list_tokens(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(HoneyToken))
            return result.scalars().all()

    The session is automatically closed after the request,
    whether it succeeds or raises an exception.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ----------------------------------------------------------------
# Lifecycle functions
# Called by main.py during application startup and shutdown.
# ----------------------------------------------------------------
async def init_db() -> None:
    """
    Validates database connectivity at application startup.
    Does NOT create tables — that is Alembic's job.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda c: c.execute(
                __import__("sqlalchemy").text("SELECT 1")
            ))
        logger.info("database_connection_verified")
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        raise


async def close_db() -> None:
    """
    Gracefully closes all database connections at shutdown.
    Prevents connection leaks when the application stops.
    """
    await engine.dispose()
    logger.info("database_connections_closed")
