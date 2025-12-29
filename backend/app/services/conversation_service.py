"""Conversation service for chat business logic."""

from __future__ import annotations

import logging
import math
from typing import Generator, Literal

from sqlalchemy.orm import Session

from app.models.message import Message
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.tool_call_repository import ToolCallRepository
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
from app.services.agent_service import (
    AgentService,
    MessageCompleteEvent,
    TextDeltaEvent,
    ToolCallEvent,
    ToolResultEvent,
)

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for conversation operations."""

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.conversation_repo = ConversationRepository(session)
        self.message_repo = MessageRepository(session)
        self.tool_call_repo = ToolCallRepository(session)
        self.agent_service = AgentService()

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
        title = self.agent_service.generate_title(first_message)

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

    def create_conversation_streaming(
        self,
        user_id: int,
        first_message: str,
    ) -> Generator[tuple[Literal["created", "delta", "end", "tool_call_start", "tool_call_end"], dict], None, None]:
        """
        Create a new conversation with AI response streaming.

        Args:
            user_id: User ID
            first_message: First user message content

        Yields:
            Tuples of (event_type, data) for SSE events:
            - ("created", {conversation, user_message_id}): Conversation created
            - ("tool_call_start", {tool_call_id, tool_name, input}): Tool call started
            - ("tool_call_end", {tool_call_id, output, error}): Tool call completed
            - ("delta", {delta}): AI response chunk
            - ("end", {assistant_message_id, content}): Streaming complete
        """
        # Generate title from first message
        title = self.agent_service.generate_title(first_message)

        # Create conversation
        conversation = self.conversation_repo.create(
            user_id=user_id,
            title=title,
        )

        # Create first message
        user_message = self.message_repo.create(
            conversation_id=conversation.id,
            role="user",
            content=first_message,
        )
        # Flush to get IDs
        self.session.flush()

        logger.info(f"Created conversation {conversation.uuid} for user {user_id}")

        # Yield conversation created event
        yield (
            "created",
            {
                "conversation": ConversationResponse.model_validate(conversation).model_dump(mode="json"),
                "user_message_id": user_message.id,
            },
        )

        # Build message history for AI (just the first message)
        messages = [{"role": "user", "content": first_message}]

        # Create placeholder for assistant message (will be updated after streaming)
        assistant_message = self.message_repo.create(
            conversation_id=conversation.id,
            role="assistant",
            content="",
        )
        self.session.flush()

        # Generate and stream AI response
        full_response = ""
        for event in self.agent_service.generate_response(messages, stream=True):
            if isinstance(event, ToolCallEvent):
                # Save tool call to database
                self.tool_call_repo.create(
                    message_id=assistant_message.id,
                    tool_call_id=event.tool_call_id,
                    tool_name=event.tool_name,
                    input_data=event.input,
                )
                yield (
                    "tool_call_start",
                    {
                        "tool_call_id": event.tool_call_id,
                        "tool_name": event.tool_name,
                        "input": event.input,
                    },
                )
            elif isinstance(event, ToolResultEvent):
                # Update tool call with result
                status = "error" if event.error else "success"
                self.tool_call_repo.update_completed(
                    tool_call_id=event.tool_call_id,
                    output=event.output,
                    error=event.error,
                    status=status,
                )
                yield (
                    "tool_call_end",
                    {
                        "tool_call_id": event.tool_call_id,
                        "output": event.output,
                        "error": event.error,
                    },
                )
            elif isinstance(event, TextDeltaEvent):
                full_response += event.delta
                yield ("delta", {"delta": event.delta})
            elif isinstance(event, MessageCompleteEvent):
                full_response = event.content

        # Update assistant message with final content
        assistant_message.content = full_response
        self.session.flush()

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

        logger.info(f"Streaming conversation created: {conversation.uuid}")

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

        # Create assistant message placeholder
        assistant_message = self.message_repo.create(
            conversation_id=conversation.id,
            role="assistant",
            content="",
        )
        self.session.flush()

        # Generate AI response using agent
        full_response = ""
        for event in self.agent_service.generate_response(messages, stream=True):
            if isinstance(event, ToolCallEvent):
                # Save tool call to database
                self.tool_call_repo.create(
                    message_id=assistant_message.id,
                    tool_call_id=event.tool_call_id,
                    tool_name=event.tool_name,
                    input_data=event.input,
                )
            elif isinstance(event, ToolResultEvent):
                # Update tool call with result
                status = "error" if event.error else "success"
                self.tool_call_repo.update_completed(
                    tool_call_id=event.tool_call_id,
                    output=event.output,
                    error=event.error,
                    status=status,
                )
            elif isinstance(event, MessageCompleteEvent):
                full_response = event.content

        # Update assistant message with final content
        assistant_message.content = full_response
        self.session.flush()

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
    ) -> Generator[tuple[Literal["start", "delta", "end", "tool_call_start", "tool_call_end"], dict], None, None]:
        """
        Send a message and get streaming AI response.

        Args:
            uuid: Conversation UUID
            user_id: User ID (for authorization check)
            content: Message content

        Yields:
            Tuples of (event_type, data) for SSE events:
            - ("start", {user_message_id}): User message saved
            - ("tool_call_start", {tool_call_id, tool_name, input}): Tool call started
            - ("tool_call_end", {tool_call_id, output, error}): Tool call completed
            - ("delta", {delta}): AI response chunk
            - ("end", {assistant_message_id, content}): Streaming complete

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

        # Create placeholder for assistant message (will be updated after streaming)
        assistant_message = self.message_repo.create(
            conversation_id=conversation.id,
            role="assistant",
            content="",
        )
        self.session.flush()

        # Generate and stream AI response
        full_response = ""
        for event in self.agent_service.generate_response(messages, stream=True):
            if isinstance(event, ToolCallEvent):
                # Save tool call to database
                self.tool_call_repo.create(
                    message_id=assistant_message.id,
                    tool_call_id=event.tool_call_id,
                    tool_name=event.tool_name,
                    input_data=event.input,
                )
                yield (
                    "tool_call_start",
                    {
                        "tool_call_id": event.tool_call_id,
                        "tool_name": event.tool_name,
                        "input": event.input,
                    },
                )
            elif isinstance(event, ToolResultEvent):
                # Update tool call with result
                status = "error" if event.error else "success"
                self.tool_call_repo.update_completed(
                    tool_call_id=event.tool_call_id,
                    output=event.output,
                    error=event.error,
                    status=status,
                )
                yield (
                    "tool_call_end",
                    {
                        "tool_call_id": event.tool_call_id,
                        "output": event.output,
                        "error": event.error,
                    },
                )
            elif isinstance(event, TextDeltaEvent):
                full_response += event.delta
                yield ("delta", {"delta": event.delta})
            elif isinstance(event, MessageCompleteEvent):
                full_response = event.content

        # Update assistant message with final content
        assistant_message.content = full_response
        self.session.flush()

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
            messages.append(
                {
                    "role": msg.role,
                    "content": msg.content,
                }
            )

        # Add new user message
        messages.append(
            {
                "role": "user",
                "content": new_content,
            }
        )

        return messages


__all__ = ["ConversationService"]
