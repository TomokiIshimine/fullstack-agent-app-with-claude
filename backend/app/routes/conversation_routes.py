"""Conversation routes for chat API."""

from __future__ import annotations

import json
import logging

from flask import Blueprint, Response, g, jsonify, request, stream_with_context
from werkzeug.exceptions import Forbidden, NotFound

from app.constants.sse_events import SERVICE_TO_SSE_EVENT_MAP, SSEEvent
from app.core.exceptions import ConversationAccessDeniedError, ConversationNotFoundError
from app.limiter import limiter
from app.routes.dependencies import validate_request_body, with_conversation_service
from app.schemas.conversation import CreateConversationRequest, SendMessageRequest
from app.services.conversation_service import ConversationService
from app.utils.auth_decorator import require_auth

logger = logging.getLogger(__name__)

conversation_bp = Blueprint("conversations", __name__, url_prefix="/conversations")


@conversation_bp.get("")
@require_auth
@with_conversation_service
def list_conversations(*, conversation_service: ConversationService):
    """
    List all conversations for the current user.

    Query parameters:
        page (int, optional): Page number (default: 1)
        per_page (int, optional): Items per page (default: 20, max: 100)

    Returns:
        {
            "conversations": [...],
            "meta": {
                "total": 45,
                "page": 1,
                "per_page": 20,
                "total_pages": 3
            }
        }
    """
    user_id = g.user_id
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    logger.info(f"GET /api/conversations - Listing conversations for user_id={user_id}")

    response = conversation_service.list_conversations(
        user_id=user_id,
        page=page,
        per_page=per_page,
    )

    logger.info(f"GET /api/conversations - Retrieved {len(response.conversations)} conversations")
    return jsonify(response.model_dump(mode="json")), 200


@conversation_bp.post("")
@require_auth
@limiter.limit("30/minute")
@with_conversation_service
@validate_request_body(CreateConversationRequest)
def create_conversation(*, data: CreateConversationRequest, conversation_service: ConversationService):
    """
    Create a new conversation with an initial message and AI response.

    Supports both streaming (SSE) and non-streaming responses.

    Request headers:
        X-Stream: "false" to disable streaming (optional, default: streaming enabled)

    Request body:
        {
            "message": "Hello, I need help with..."
        }

    Streaming response (default):
        SSE events:
        - event: conversation_created, data: {"conversation": {...}, "user_message_id": 1}
        - event: tool_call_start, data: {"tool_call_id": "...", "tool_name": "...", "input": {...}}
        - event: tool_call_end, data: {"tool_call_id": "...", "output": "...", "error": null}
        - event: content_delta, data: {"delta": "..."}
        - event: message_end, data: {"assistant_message_id": 2, "content": "..."}
        - event: error, data: {"error": "...", "user_message_id": 1} (if AI fails after user message saved)

    Non-streaming response:
        {
            "conversation": {...},
            "message": {...},
            "assistant_message": {...}
        }
    """
    user_id = g.user_id
    stream = request.headers.get("X-Stream", "true").lower() != "false"

    logger.info(f"POST /api/conversations - Creating conversation for user_id={user_id}, stream={stream}")

    if stream:
        # Streaming response using SSE
        def generate():
            user_message_id = None
            try:
                for event_type, event_data in conversation_service.create_conversation_streaming(
                    user_id=user_id,
                    first_message=data.message,
                ):
                    if event_type == "created":
                        user_message_id = event_data.get("user_message_id")
                    sse_event = SERVICE_TO_SSE_EVENT_MAP.get(event_type)
                    if sse_event:
                        yield f"event: {sse_event}\ndata: {json.dumps(event_data)}\n\n"
            except Exception as exc:
                logger.error("Error during conversation creation streaming", exc_info=True)
                is_known_error = isinstance(exc, (ConversationNotFoundError, ConversationAccessDeniedError))
                error_data = {"error": str(exc) if is_known_error else "Internal server error"}
                if user_message_id is not None:
                    error_data["user_message_id"] = user_message_id
                yield f"event: {SSEEvent.ERROR}\ndata: {json.dumps(error_data)}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )
    else:
        # Non-streaming response
        response = conversation_service.create_conversation(
            user_id=user_id,
            first_message=data.message,
        )
        logger.info(f"POST /api/conversations - Created conversation {response.conversation.uuid}")
        return jsonify(response.model_dump(mode="json")), 201


@conversation_bp.get("/<uuid>")
@require_auth
@with_conversation_service
def get_conversation(uuid: str, *, conversation_service: ConversationService):
    """
    Get a conversation with all messages.

    Path parameters:
        uuid: Conversation UUID

    Returns:
        {
            "conversation": {...},
            "messages": [...]
        }
    """
    user_id = g.user_id
    logger.info(f"GET /api/conversations/{uuid} - Retrieving conversation for user_id={user_id}")

    response = conversation_service.get_conversation(
        uuid=uuid,
        user_id=user_id,
    )

    logger.info(f"GET /api/conversations/{uuid} - Retrieved {len(response.messages)} messages")
    return jsonify(response.model_dump(mode="json")), 200


@conversation_bp.delete("/<uuid>")
@require_auth
@with_conversation_service
def delete_conversation(uuid: str, *, conversation_service: ConversationService):
    """
    Delete a conversation.

    Path parameters:
        uuid: Conversation UUID

    Returns:
        204 No Content on success
    """
    user_id = g.user_id
    logger.info(f"DELETE /api/conversations/{uuid} - Deleting conversation for user_id={user_id}")

    conversation_service.delete_conversation(
        uuid=uuid,
        user_id=user_id,
    )

    logger.info(f"DELETE /api/conversations/{uuid} - Deleted successfully")
    return "", 204


@conversation_bp.post("/<uuid>/messages")
@require_auth
@limiter.limit("30/minute")
@with_conversation_service
@validate_request_body(SendMessageRequest)
def send_message(uuid: str, *, data: SendMessageRequest, conversation_service: ConversationService):
    """
    Send a message and get AI response.

    Supports both streaming (SSE) and non-streaming responses.

    Path parameters:
        uuid: Conversation UUID

    Request headers:
        X-Stream: "false" to disable streaming (optional, default: streaming enabled)

    Request body:
        {
            "content": "Your message here"
        }

    Streaming response (default):
        SSE events:
        - event: message_start, data: {"user_message_id": 1}
        - event: tool_call_start, data: {"tool_call_id": "...", "tool_name": "...", "input": {...}}
        - event: tool_call_end, data: {"tool_call_id": "...", "output": "...", "error": null}
        - event: content_delta, data: {"delta": "..."}
        - event: message_end, data: {"assistant_message_id": 2, "content": "..."}
        - event: error, data: {"error": "...", "user_message_id": 1} (if AI fails after user message saved)

    Non-streaming response:
        {
            "user_message": {...},
            "assistant_message": {...}
        }
    """
    user_id = g.user_id
    stream = request.headers.get("X-Stream", "true").lower() != "false"

    logger.info(f"POST /api/conversations/{uuid}/messages - Sending message for user_id={user_id}, stream={stream}")

    if stream:
        # Validate conversation access BEFORE starting stream
        # This allows proper HTTP error codes (404/403) to be returned
        try:
            conversation_service.validate_conversation_access(uuid=uuid, user_id=user_id)
        except ConversationNotFoundError as exc:
            raise NotFound(description=str(exc)) from exc
        except ConversationAccessDeniedError as exc:
            raise Forbidden(description=str(exc)) from exc

        # Streaming response using SSE
        def generate():
            user_message_id = None
            try:
                for event_type, event_data in conversation_service.send_message_streaming(
                    uuid=uuid,
                    user_id=user_id,
                    content=data.content,
                ):
                    if event_type == "start":
                        user_message_id = event_data.get("user_message_id")
                    sse_event = SERVICE_TO_SSE_EVENT_MAP.get(event_type)
                    if sse_event:
                        yield f"event: {sse_event}\ndata: {json.dumps(event_data)}\n\n"
            except Exception as exc:
                logger.error("Error during streaming", exc_info=True)
                # Include user_message_id in error so client knows data was persisted
                is_known_error = isinstance(exc, (ConversationNotFoundError, ConversationAccessDeniedError))
                error_data = {"error": str(exc) if is_known_error else "Internal server error"}
                if user_message_id is not None:
                    error_data["user_message_id"] = user_message_id
                yield f"event: {SSEEvent.ERROR}\ndata: {json.dumps(error_data)}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )
    else:
        # Non-streaming response
        response = conversation_service.send_message(
            uuid=uuid,
            user_id=user_id,
            content=data.content,
        )
        logger.info(f"POST /api/conversations/{uuid}/messages - Message exchange completed")
        return jsonify(response.model_dump(mode="json")), 200


__all__ = ["conversation_bp"]
