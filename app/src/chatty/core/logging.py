"""
Logging configuration and utilities.
"""

import logging
import os
import sys
from typing import Any

import structlog
from structlog.stdlib import LoggerFactory

LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def _get_log_level() -> int:
    """Resolve log level from LOG_LEVEL env var."""
    name = os.environ.get("LOG_LEVEL", "DEBUG").upper()
    return LOG_LEVEL_MAP.get(name, logging.DEBUG)


def configure_logging() -> None:
    """Configure structured logging for the application."""
    level = _get_log_level()

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_request_info(
    method: str,
    path: str,
    headers: dict[str, str],
    query_params: dict[str, Any],
    client_ip: str,
    user_agent: str,
) -> None:
    """Log request information."""
    logger = get_logger("http.request")
    logger.info(
        "Incoming request",
        method=method,
        path=path,
        client_ip=client_ip,
        user_agent=user_agent,
        query_params=query_params,
        headers=_sanitize_headers(headers),
    )


def log_response_info(
    method: str,
    path: str,
    status_code: int,
    response_time_ms: float,
    client_ip: str,
) -> None:
    """Log response information."""
    logger = get_logger("http.response")
    logger.info(
        "Response sent",
        method=method,
        path=path,
        status_code=status_code,
        response_time_ms=round(response_time_ms, 2),
        client_ip=client_ip,
    )


def log_error(
    method: str,
    path: str,
    status_code: int,
    error_message: str,
    exception: Exception | None = None,
    client_ip: str | None = None,
) -> None:
    """Log error information."""
    logger = get_logger("http.error")
    log_data = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "error_message": error_message,
        "client_ip": client_ip,
    }

    if exception:
        log_data["exception_type"] = type(exception).__name__
        log_data["exception"] = str(exception)

    logger.error("Request error occurred", **log_data)


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """Remove sensitive headers from logging."""
    sensitive_headers = {
        "authorization",
        "cookie",
        "x-api-key",
        "x-auth-token",
    }

    sanitized = {}
    for key, value in headers.items():
        if key.lower() in sensitive_headers:
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value

    return sanitized
