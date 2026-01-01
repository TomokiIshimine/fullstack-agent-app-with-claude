"""CSRF protection utilities."""

from __future__ import annotations

import logging
import secrets
from typing import Iterable

from flask import request
from werkzeug.exceptions import Forbidden

from app.config import load_cookie_config

logger = logging.getLogger(__name__)

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
SAFE_METHODS: Iterable[str] = {"GET", "HEAD", "OPTIONS"}


def generate_csrf_token() -> str:
    """Generate a new CSRF token."""
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response, max_age: int | None = None) -> str:
    """Set CSRF token cookie on the response.

    Returns:
        The generated CSRF token.
    """
    token = generate_csrf_token()
    cookie_config = load_cookie_config()

    response.set_cookie(
        CSRF_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=False,
        secure=cookie_config.secure,
        samesite=cookie_config.samesite,
        path="/",
        domain=cookie_config.domain,
    )

    return token


def clear_csrf_cookie(response) -> None:
    """Clear CSRF token cookie on the response."""
    cookie_config = load_cookie_config()
    response.set_cookie(
        CSRF_COOKIE_NAME,
        value="",
        max_age=0,
        httponly=False,
        secure=cookie_config.secure,
        samesite=cookie_config.samesite,
        path="/",
        domain=cookie_config.domain,
    )


def validate_csrf_token() -> None:
    """Validate CSRF token for unsafe HTTP methods."""
    if request.method in SAFE_METHODS:
        return

    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    csrf_header = request.headers.get(CSRF_HEADER_NAME)

    if not csrf_cookie or not csrf_header:
        logger.warning("CSRF token missing")
        raise Forbidden("CSRFトークンが必要です")

    if not secrets.compare_digest(csrf_cookie, csrf_header):
        logger.warning("CSRF token mismatch")
        raise Forbidden("CSRFトークンが不正です")


__all__ = [
    "CSRF_COOKIE_NAME",
    "CSRF_HEADER_NAME",
    "clear_csrf_cookie",
    "generate_csrf_token",
    "set_csrf_cookie",
    "validate_csrf_token",
]
