"""Admin conversation routes for viewing all users' conversation history."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

from app.constants.http import HTTP_OK
from app.constants.pagination import DEFAULT_PER_PAGE
from app.routes.dependencies import validate_uuid_param, with_admin_conversation_service
from app.services.admin_conversation_service import AdminConversationService
from app.utils.auth_decorator import require_auth, require_role
from app.utils.date_filter import parse_date_filter

logger = logging.getLogger(__name__)

admin_conversation_bp = Blueprint("admin_conversations", __name__, url_prefix="/admin/conversations")


@admin_conversation_bp.get("")
@require_auth
@require_role("admin")
@with_admin_conversation_service
def list_all_conversations(*, admin_conversation_service: AdminConversationService):
    """
    List all conversations endpoint (Admin only).

    Query parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)
        - user_id: Filter by user ID (optional)
        - start_date: Filter by start date in ISO format (optional)
        - end_date: Filter by end date in ISO format (optional)

    Returns:
        {
            "conversations": [
                {
                    "uuid": "...",
                    "title": "...",
                    "message_count": 5,
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "name": "User Name"
                    },
                    "created_at": "2025-10-01T10:00:00Z",
                    "updated_at": "2025-10-01T12:00:00Z"
                },
                ...
            ],
            "meta": {
                "total": 100,
                "page": 1,
                "per_page": 20,
                "total_pages": 5
            }
        }
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", DEFAULT_PER_PAGE, type=int)
    user_id = request.args.get("user_id", type=int)
    start_date = request.args.get("start_date", type=str)
    end_date = request.args.get("end_date", type=str)

    # Validate date format if provided
    if start_date and parse_date_filter(start_date) is None:
        raise BadRequest("開始日の形式が不正です。ISO形式（例: 2025-01-01）で指定してください")
    if end_date and parse_date_filter(end_date) is None:
        raise BadRequest("終了日の形式が不正です。ISO形式（例: 2025-01-01）で指定してください")

    logger.info(
        "GET /api/admin/conversations - Retrieving all conversations",
        extra={
            "page": page,
            "per_page": per_page,
            "user_id_filter": user_id,
            "start_date_filter": start_date,
            "end_date_filter": end_date,
        },
    )

    response = admin_conversation_service.list_all_conversations(
        page=page,
        per_page=per_page,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    logger.info(
        f"GET /api/admin/conversations - Retrieved {len(response.conversations)} conversations",
        extra={"total": response.meta.total},
    )
    return jsonify(response.model_dump()), HTTP_OK


@admin_conversation_bp.get("/<uuid>")
@require_auth
@require_role("admin")
@validate_uuid_param("uuid")
@with_admin_conversation_service
def get_conversation_detail(uuid: str, *, admin_conversation_service: AdminConversationService):
    """
    Get conversation detail endpoint (Admin only).

    Args:
        uuid: Conversation UUID

    Returns:
        {
            "uuid": "...",
            "title": "...",
            "user": {
                "id": 1,
                "email": "user@example.com",
                "name": "User Name"
            },
            "messages": [...],
            "created_at": "2025-10-01T10:00:00Z",
            "updated_at": "2025-10-01T12:00:00Z"
        }
    """
    logger.info(
        "GET /api/admin/conversations/<uuid> - Retrieving conversation detail",
        extra={"conversation_uuid": uuid},
    )

    response = admin_conversation_service.get_conversation_detail(uuid)

    logger.info(
        "GET /api/admin/conversations/<uuid> - Retrieved conversation detail",
        extra={"conversation_uuid": uuid, "message_count": len(response.messages)},
    )
    return jsonify(response.model_dump()), HTTP_OK


__all__ = ["admin_conversation_bp"]
