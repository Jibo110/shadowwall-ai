"""
Alembic migration environment configuration.

This file tells Alembic:
1. Where to find the database (from our Settings)
2. Which models to track for schema changes (our Base metadata)
3. How to run migrations (async, using asyncpg)
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.db.engine import Base

# Import all models here so Alembic can detect them.
# Every new model file you create must be imported here.
from app.db.models import token  # noqa: F401
from app.db.models import event  # noqa: F401
from app.db.models import user  # noqa: F401

# Alembic config object — reads from alembic.ini
config = context.config

# Configure Python logging from alembic.ini settings
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is the metadata object Alembic inspects to detect
# schema changes. It must include ALL your models.
target_metadata = Base.metadata

# Override the sqlalchemy.url from alembic.ini with our
# validated settings — single source of truth.
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """
    Run migrations without a live database connection.
    Useful for generating SQL scripts to review before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        # compare_type=True means Alembic detects column type changes
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using async engine — required for asyncpg."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # NullPool = no connection pooling during migrations
        # Each migration gets a fresh connection
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for running migrations against a live database."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
