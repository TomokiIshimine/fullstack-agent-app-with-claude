"""Password management routes for changing passwords."""

from __future__ import annotations

import logging

from flask import Blueprint, g, jsonify

from app.routes.dependencies import validate_request_body, with_password_service
from app.schemas.password import PasswordChangeRequest, PasswordChangeResponse
from app.services.password_service import PasswordService
from app.utils.auth_decorator import require_auth

logger = logging.getLogger(__name__)

password_bp = Blueprint("password", __name__, url_prefix="/password")


@password_bp.post("/change")
@require_auth
@with_password_service
@validate_request_body(PasswordChangeRequest)
def change_password(*, data: PasswordChangeRequest, password_service: PasswordService):
    """
    Change password endpoint (all authenticated users).

    Request body:
        {
            "current_password": "oldpassword123",
            "new_password": "newpassword123"
        }

    Returns:
        {
            "message": "パスワードを変更しました"
        }
    """
    user_id = g.user_id
    logger.info(f"POST /api/password/change - Changing password for user_id={user_id}")

    password_service.change_password(
        user_id=user_id,
        current_password=data.current_password,
        new_password=data.new_password,
    )

    response = PasswordChangeResponse(message="パスワードを変更しました")
    logger.info(f"POST /api/password/change - Password changed successfully for user_id={user_id}")
    return jsonify(response.model_dump()), 200


__all__ = ["password_bp"]
