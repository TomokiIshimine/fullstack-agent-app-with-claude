"""Authentication routes for login, logout, and token refresh."""

from __future__ import annotations

import logging
import os

from flask import Blueprint, jsonify, make_response, request
from werkzeug.exceptions import Unauthorized

from app.limiter import limiter
from app.routes.dependencies import validate_request_body, with_auth_service
from app.schemas.auth import LoginRequest, LogoutResponse, RefreshTokenResponse, UserResponse
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _set_auth_cookies(response, access_token: str, refresh_token: str):
    """Helper to set authentication cookies on response."""
    cookie_secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    cookie_domain = os.getenv("COOKIE_DOMAIN", None)

    access_token_max_age = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) * 60
    refresh_token_max_age = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")) * 24 * 60 * 60

    response.set_cookie(
        "access_token",
        value=access_token,
        max_age=access_token_max_age,
        httponly=True,
        secure=cookie_secure,
        samesite="Lax",
        path="/api",
        domain=cookie_domain,
    )

    response.set_cookie(
        "refresh_token",
        value=refresh_token,
        max_age=refresh_token_max_age,
        httponly=True,
        secure=cookie_secure,
        samesite="Lax",
        path="/api",
        domain=cookie_domain,
    )


def _clear_auth_cookies(response):
    """Helper to clear authentication cookies on response."""
    cookie_domain = os.getenv("COOKIE_DOMAIN", None)

    response.set_cookie("access_token", value="", max_age=0, httponly=True, samesite="Lax", path="/api", domain=cookie_domain)
    response.set_cookie("refresh_token", value="", max_age=0, httponly=True, samesite="Lax", path="/api", domain=cookie_domain)


@auth_bp.post("/login")
@limiter.limit("10 per minute")
@with_auth_service
@validate_request_body(LoginRequest)
def login(*, data: LoginRequest, auth_service: AuthService):
    """
    Login endpoint.

    Request body:
        {
            "email": "user@example.com",
            "password": "password123"
        }

    Returns:
        {
            "user": {
                "id": 1,
                "email": "user@example.com"
            }
        }

    Sets httpOnly cookies:
        - access_token: JWT access token (expires in 1 day)
        - refresh_token: JWT refresh token (expires in 7 days)
    """
    response_data, access_token, refresh_token = auth_service.login(data.email, data.password)

    response = make_response(jsonify(response_data.model_dump()), 200)
    _set_auth_cookies(response, access_token, refresh_token)

    logger.info(f"Login successful: {data.email}")
    return response


@auth_bp.post("/refresh")
@limiter.limit("30 per minute")
@with_auth_service
def refresh(*, auth_service: AuthService):
    """
    Refresh access token endpoint.

    Reads refresh_token from cookies and generates new tokens.

    Returns:
        {
            "message": "トークンを更新しました",
            "user": {
                "id": 1,
                "email": "user@example.com"
            }
        }

    Sets httpOnly cookies:
        - access_token: New JWT access token
        - refresh_token: New JWT refresh token
    """
    # Get refresh token from cookies
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        logger.warning("Refresh token not found in cookies")
        raise Unauthorized("リフレッシュトークンが必要です")

    # Refresh tokens
    new_access_token, new_refresh_token, user = auth_service.refresh_access_token(refresh_token)

    # Create response with user information
    user_response = UserResponse.model_validate(user, from_attributes=True)
    response_data = RefreshTokenResponse(message="トークンを更新しました", user=user_response)
    response = make_response(jsonify(response_data.model_dump()), 200)

    _set_auth_cookies(response, new_access_token, new_refresh_token)

    logger.info("Token refresh successful")
    return response


@auth_bp.post("/logout")
@limiter.limit("20 per minute")
@with_auth_service
def logout(*, auth_service: AuthService):
    """
    Logout endpoint.

    Revokes refresh token and clears cookies.

    Returns:
        {
            "message": "ログアウトしました"
        }

    Clears cookies:
        - access_token
        - refresh_token
    """
    # Get refresh token from cookies
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        # Revoke refresh token
        auth_service.logout(refresh_token)

    # Create response
    response_data = LogoutResponse(message="ログアウトしました")
    response = make_response(jsonify(response_data.model_dump()), 200)
    _clear_auth_cookies(response)

    logger.info("Logout successful")
    return response


__all__ = ["auth_bp"]
