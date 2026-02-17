"""User setting routes for managing user preferences."""

from __future__ import annotations

import logging

from flask import Blueprint, g, jsonify

from app.constants.http import HTTP_OK
from app.routes.dependencies import validate_request_body, with_user_setting_service
from app.schemas.user_setting import UserSettingsResponse, UserSettingsUpdateRequest, UserSettingsUpdateResponse
from app.services.user_setting_service import UserSettingService
from app.utils.auth_decorator import require_auth

logger = logging.getLogger(__name__)

user_setting_bp = Blueprint("user_settings", __name__, url_prefix="/users")


@user_setting_bp.get("/me/settings")
@require_auth
@with_user_setting_service
def get_settings(*, user_setting_service: UserSettingService):
    """
    Get current user's settings.

    Returns:
        {
            "send_shortcut": "enter"
        }
    """
    user_id = g.user_id
    logger.info(f"GET /api/users/me/settings - Getting settings for user_id={user_id}")

    settings = user_setting_service.get_settings(user_id)

    response = UserSettingsResponse(**settings)
    return jsonify(response.model_dump()), HTTP_OK


@user_setting_bp.patch("/me/settings")
@require_auth
@with_user_setting_service
@validate_request_body(UserSettingsUpdateRequest)
def update_settings(*, data: UserSettingsUpdateRequest, user_setting_service: UserSettingService):
    """
    Update current user's settings.

    Request body:
        {
            "send_shortcut": "ctrl_enter"
        }

    Returns:
        {
            "message": "設定を更新しました",
            "send_shortcut": "ctrl_enter"
        }
    """
    user_id = g.user_id
    logger.info(f"PATCH /api/users/me/settings - Updating settings for user_id={user_id}")

    result = user_setting_service.update_settings(user_id=user_id, send_shortcut=data.send_shortcut)

    response = UserSettingsUpdateResponse(
        message="設定を更新しました",
        send_shortcut=result["send_shortcut"],
    )
    logger.info(f"PATCH /api/users/me/settings - Settings updated successfully for user_id={user_id}")
    return jsonify(response.model_dump()), HTTP_OK


__all__ = ["user_setting_bp"]
