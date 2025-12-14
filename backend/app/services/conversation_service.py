"""Conversation service for chat business logic."""

from __future__ import annotations

import logging
import math
from typing import Generator, Literal

from sqlalchemy.orm import Session

from app.models.message import Message
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.conversation import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationWithCountResponse,
    CreateConversationResponse,
    MessageResponse,
    PaginationMeta,
    SendMessageResponse,
)
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for conversation operations."""

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.conversation_repo = ConversationRepository(session)
        self.message_repo = MessageRepository(session)
        self.ai_service = AIService()

    def list_conversations(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
    ) -> ConversationListResponse:
        """
        List conversations for a user with pagination.

        Args:
            user_id: User ID
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            ConversationListResponse with conversations and pagination meta
        """
        # Clamp per_page to reasonable limits
        per_page = max(1, min(per_page, 100))
        page = max(1, page)

        conversations_with_count, total = self.conversation_repo.find_by_user_id_with_message_count(
            user_id=user_id,
            page=page,
            per_page=per_page,
        )

        total_pages = math.ceil(total / per_page) if total > 0 else 1

        conversations = [
            ConversationWithCountResponse(
                uuid=item["conversation"].uuid,
                title=item["conversation"].title,
                message_count=item["message_count"],
                created_at=item["conversation"].created_at,
                updated_at=item["conversation"].updated_at,
            )
            for item in conversations_with_count
        ]

        return ConversationListResponse(
            conversations=conversations,
            meta=PaginationMeta(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
            ),
        )

    def get_conversation(
        self,
        uuid: str,
        user_id: int,
    ) -> ConversationDetailResponse:
        """
        Get a conversation with all messages.

        Args:
            uuid: Conversation UUID
            user_id: User ID (for authorization check)

        Returns:
            ConversationDetailResponse with conversation and messages

        Raises:
            ValueError: If conversation not found
            PermissionError: If user doesn't own the conversation
        """
        conversation = self.conversation_repo.find_by_uuid_with_messages(uuid)

        if not conversation:
            raise ValueError("Conversation not found")

        if conversation.user_id != user_id:
            raise PermissionError("Access denied")

        return ConversationDetailResponse(
            conversation=ConversationResponse.model_validate(conversation),
            messages=[MessageResponse.model_validate(msg) for msg in conversation.messages],
        )

    def create_conversation(
        self,
        user_id: int,
        first_message: str,
    ) -> CreateConversationResponse:
        """
        Create a new conversation with the first message.

        Args:
            user_id: User ID
            first_message: First user message content

        Returns:
            CreateConversationResponse with conversation and message
        """
        # Generate title from first message
        title = self.ai_service.generate_title(first_message)

        # Create conversation
        conversation = self.conversation_repo.create(
            user_id=user_id,
            title=title,
        )

        # Create first message
        message = self.message_repo.create(
            conversation_id=conversation.id,
            role="user",
            content=first_message,
        )

        logger.info(f"Created conversation {conversation.uuid} for user {user_id}")

        return CreateConversationResponse(
            conversation=ConversationResponse.model_validate(conversation),
            message=MessageResponse.model_validate(message),
        )

    def delete_conversation(
        self,
        uuid: str,
        user_id: int,
    ) -> None:
        """
        Delete a conversation.

        Args:
            uuid: Conversation UUID
            user_id: User ID (for authorization check)

        Raises:
            ValueError: If conversation not found
            PermissionError: If user doesn't own the conversation
        """
        conversation = self.conversation_repo.find_by_uuid(uuid)

        if not conversation:
            raise ValueError("Conversation not found")

        if conversation.user_id != user_id:
            raise PermissionError("Access denied")

        self.conversation_repo.delete(conversation)
        logger.info(f"Deleted conversation {uuid}")

    def validate_conversation_access(
        self,
        uuid: str,
        user_id: int,
    ) -> None:
        """
        Validate that a conversation exists and user has access.

        Args:
            uuid: Conversation UUID
            user_id: User ID

        Raises:
            ValueError: If conversation not found
            PermissionError: If user doesn't own the conversation
        """
        conversation = self.conversation_repo.find_by_uuid(uuid)

        if not conversation:
            raise ValueError("Conversation not found")

        if conversation.user_id != user_id:
            raise PermissionError("Access denied")

    def send_message(
        self,
        uuid: str,
        user_id: int,
        content: str,
    ) -> SendMessageResponse:
        """
        Send a message and get AI response (non-streaming).

        Args:
            uuid: Conversation UUID
            user_id: User ID (for authorization check)
            content: Message content

        Returns:
            SendMessageResponse with user and assistant messages

        Raises:
            ValueError: If conversation not found
            PermissionError: If user doesn't own the conversation
        """
        conversation = self.conversation_repo.find_by_uuid_with_messages(uuid)

        if not conversation:
            raise ValueError("Conversation not found")

        if conversation.user_id != user_id:
            raise PermissionError("Access denied")

        # Save user message
        user_message = self.message_repo.create(
            conversation_id=conversation.id,
            role="user",
            content=content,
        )

        # Build message history for AI
        messages = self._build_message_history(conversation.messages, content)

        # Generate AI response (stream=False returns str)
        ai_response = self.ai_service.generate_response(messages, stream=False)
        if not isinstance(ai_response, str):
            raise RuntimeError("Expected string response from AI service")

        # Save assistant message
        assistant_message = self.message_repo.create(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_response,
        )

        # Update conversation timestamp
        self.conversation_repo.touch(conversation)

        logger.info(f"Message exchange in conversation {uuid}")

        return SendMessageResponse(
            user_message=MessageResponse.model_validate(user_message),
            assistant_message=MessageResponse.model_validate(assistant_message),
        )

    def send_message_streaming(
        self,
        uuid: str,
        user_id: int,
        content: str,
    ) -> Generator[tuple[Literal["start", "delta", "end"], dict], None, None]:
        """
        Send a message and get streaming AI response.

        Args:
            uuid: Conversation UUID
            user_id: User ID (for authorization check)
            content: Message content

        Yields:
            Tuples of (event_type, data) for SSE events

        Raises:
            ValueError: If conversation not found
            PermissionError: If user doesn't own the conversation
        """
        conversation = self.conversation_repo.find_by_uuid_with_messages(uuid)

        if not conversation:
            raise ValueError("Conversation not found")

        if conversation.user_id != user_id:
            raise PermissionError("Access denied")

        # Save user message
        user_message = self.message_repo.create(
            conversation_id=conversation.id,
            role="user",
            content=content,
        )
        # Flush to get message ID
        self.session.flush()

        # Build message history for AI
        messages = self._build_message_history(conversation.messages, content)

        # Yield start event
        yield ("start", {"user_message_id": user_message.id})

        # Generate and stream AI response
        full_response = ""
        for chunk in self.ai_service.generate_response(messages, stream=True):
            full_response += chunk
            yield ("delta", {"delta": chunk})

        # Save assistant message
        assistant_message = self.message_repo.create(
            conversation_id=conversation.id,
            role="assistant",
            content=full_response,
        )

        # Update conversation timestamp
        self.conversation_repo.touch(conversation)

        # Yield end event
        yield (
            "end",
            {
                "assistant_message_id": assistant_message.id,
                "content": full_response,
            },
        )

        logger.info(f"Streaming message exchange in conversation {uuid}")

    def _build_message_history(
        self,
        existing_messages: list[Message],
        new_content: str,
    ) -> list[dict]:
        """
        Build message history for AI API call.

        Args:
            existing_messages: Existing messages in conversation
            new_content: New user message content

        Returns:
            List of message dicts for AI API
        """
        messages = []

        # Add existing messages
        for msg in existing_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        # Add new user message
        messages.append({
            "role": "user",
            "content": new_content,
        })

        return messages


__all__ = ["ConversationService"]
