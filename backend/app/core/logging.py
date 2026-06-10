"""
Structured logging configuration for ShadowWall AI.

We use structlog instead of Python's standard logging module because
it produces machine-readable JSON logs in production and clean,
human-readable colored logs in development — from the same codebase.

Every log entry in this system is a structured event with consistent
fields: timestamp, level, service, and the event message. This makes
logs queryable in tools like Grafana Loki or AWS CloudWatch.
"""

import logging
import sys

import structlog

from app.core.config import get_settings


def setup_logging() -> None:
    """
    Configure structlog for the entire application.

    Call this ONCE at application startup in main.py.
    After this runs, every module in the app can do:

        import structlog
        logger = structlog.get_logger()
        logger.info("event_name", key="value", another_key=123)
    """
    settings = get_settings()

    # Define the processing pipeline — every log entry passes through
    # these processors in order, left to right.
    shared_processors: list[structlog.types.Processor] = [
        # Adds the log level (info, warning, error) to every entry
        structlog.stdlib.add_log_level,
        # Adds timestamps in ISO 8601 format
        structlog.processors.TimeStamper(fmt="iso"),
        # Renders exception tracebacks cleanly
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.is_production:
        # Production: output pure JSON — one log entry per line.
        # This format is consumed by log aggregators (Datadog, Loki, etc.)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: output colored, human-readable console logs.
        # Same data, different presentation.
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            # In development we show DEBUG and above.
            # In production we show INFO and above (less noise).
            logging.DEBUG if settings.is_development else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """
    Returns a bound logger instance for a given module.

    Usage in any module:

        from app.core.logging import get_logger
        logger = get_logger(__name__)

        logger.info("honey_token_triggered", token_id="abc123", ip="1.2.3.4")
        logger.warning("rate_limit_exceeded", ip="1.2.3.4", endpoint="/api/v1/tokens")
        logger.error("database_connection_failed", error=str(e))

    The key=value pairs become searchable fields in your log system.
    """
    return structlog.get_logger(name)
