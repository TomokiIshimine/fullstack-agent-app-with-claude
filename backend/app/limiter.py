"""Rate limiting middleware using Flask-Limiter with Redis backend."""

from __future__ import annotations

import logging

from flask import Flask, Response, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import TooManyRequests

from app.config import get_rate_limit_storage_uri, load_rate_limit_config

logger = logging.getLogger(__name__)


def _init_limiter_storage_uri() -> str:
    """
    Get storage URI for Flask-Limiter at module load time.

    Returns:
        Redis URI if configured and enabled, otherwise "memory://" for in-memory storage

    Note:
        This function is called at module import time, before Flask app initialization.
        It reads directly from environment variables via config.
    """
    config = load_rate_limit_config()
    uri = get_rate_limit_storage_uri(config)

    if not config.enabled:
        logger.info("Rate limiting is disabled (RATE_LIMIT_ENABLED=false), using memory storage")
    elif not config.redis_host:
        logger.warning("REDIS_HOST not configured, using memory storage for rate limiting")
    else:
        # Log connection (mask password)
        safe_uri = f"redis://{'***@' if config.redis_password else ''}{config.redis_host}:{config.redis_port}/0"
        logger.info(f"Configured Redis storage for rate limiting: {safe_uri}")

    return uri


# Load rate limit configuration
_rate_limit_config = load_rate_limit_config()

# Global limiter instance with proper storage configuration
# Storage URI is determined at module load time from environment variables
limiter = Limiter(
    key_func=get_remote_address,  # Use client IP as rate limit key
    storage_uri=_init_limiter_storage_uri(),  # Redis or memory storage
    storage_options={"socket_connect_timeout": 30, "socket_timeout": 30},
    # Default limits (can be overridden per route)
    default_limits=list(_rate_limit_config.default_limits),
    # Swallow errors (don't fail requests if Redis is down)
    swallow_errors=_rate_limit_config.swallow_errors,
    # Headers in response
    headers_enabled=_rate_limit_config.headers_enabled,
    # Strategy: fixed-window (simple and performant)
    strategy=_rate_limit_config.strategy,
)


def rate_limit_error_handler(e: TooManyRequests) -> tuple[Response, int]:
    """
    Custom error handler for rate limit exceeded (429) responses.

    Args:
        e: TooManyRequests exception

    Returns:
        JSON error response with 429 status code
    """
    logger.warning(f"Rate limit exceeded: {e.description}")
    return jsonify({"error": "リクエストが多すぎます。しばらく待ってから再試行してください。"}), 429


def init_limiter(app: Flask) -> Limiter:
    """
    Initialize Flask-Limiter with Flask application.

    Args:
        app: Flask application instance

    Returns:
        Configured Limiter instance

    Note:
        The limiter is already configured with storage URI at module load time.
        This function binds the limiter to the Flask app and registers error handlers.
    """
    # Bind limiter to Flask app
    limiter.init_app(app)

    # Register custom error handler for 429 responses
    app.register_error_handler(429, rate_limit_error_handler)

    # Log the storage backend being used
    if limiter._storage and hasattr(limiter._storage, "storage_uri"):
        storage_uri = limiter._storage.storage_uri
        if "redis" in str(storage_uri):
            logger.info("Rate limiter initialized with Redis backend")
        else:
            logger.info("Rate limiter initialized with in-memory backend")
    else:
        logger.info("Rate limiter initialized with in-memory backend")

    return limiter


__all__ = ["init_limiter", "limiter"]
