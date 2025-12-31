"""Conversation service for chat business logic."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Generator, Literal

from sqlalchemy.orm import Session

from app.constants.pagination import DEFAULT_PER_PAGE, MAX_PER_PAGE, MIN_PER_PAGE
from app.core.exceptions import ConversationAccessDeniedError, ConversationNotFoundError
from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.tool_call_repository import ToolCallData, ToolCallRepository
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
from app.schemas.tool_call import ToolCallResponse
from app.services.agent_service import (
    AgentEvent,
    AgentService,
    MessageCompleteEvent,
    MessageMetadataEvent,
    RetryEvent,
    TextDeltaEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from app.services.metadata_service import MetadataService, StreamingResult


@dataclass
class AgentStreamingResult:
    """Result from streaming agent response with metadata and buffered tool calls.

    This class extends StreamingResult to include buffered tool call data
    for batch database operations after streaming completes.
    """

    streaming_result: StreamingResult
    tool_calls: list[ToolCallData] = field(default_factory=list)


logger = logging.getLogger(__name__)

# Type alias for streaming event tuples
StreamingEvent = tuple[
    Literal["created", "start", "end", "delta", "tool_call_start", "tool_call_end", "retry"],
    dict,
]


class ConversationService:
    """Service for conversation operations."""

    def __init__(
        self,
        session: Session,
        agent_service: AgentService | None = None,
        metadata_service: MetadataService | None = None,
    ):
        """Initialize service with database session.

        Args:
            session: SQLAlchemy database session.
            agent_service: Agent service instance. If None, creates lazily on first use.
            metadata_service: Metadata service instance. If None, creates default instance.
        """
        self.session = session
        self.conversation_repo = ConversationRepository(session)
        self.message_repo = MessageRepository(session)
        self.tool_call_repo = ToolCallRepository(session)
        self._agent_service: AgentService | None = agent_service
        self.metadata_service = metadata_service or MetadataService()

    @property
    def agent_service(self) -> AgentService:
        """Get agent service, creating it lazily if needed.

        Returns:
            AgentService instance.
        """
        if self._agent_service is None:
            self._agent_service = AgentService()
        return self._agent_service

    def list_conversations(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE,
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
        per_page = max(MIN_PER_PAGE, min(per_page, MAX_PER_PAGE))
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
            ConversationNotFoundError: If conversation not found
            ConversationAccessDeniedError: If user doesn't own the conversation
        """
        conversation = self.validate_conversation_access(uuid, user_id, with_messages=True)

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
    ) -> Generator[StreamingEvent, None, None]:
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

        # Generate and stream AI response using common method
        # Tool call buffer is passed to allow persistence on abort
        tool_call_buffer: dict[str, ToolCallData] = {}
        response_generator = self._stream_agent_response(messages, tool_call_buffer)
        result: AgentStreamingResult | None = None
        streaming_completed = False
        try:
            try:
                while True:
                    streaming_event = next(response_generator)
                    yield streaming_event
            except StopIteration as e:
                result = e.value
                streaming_completed = True

            # Finalize and yield end event (only on successful completion)
            if result is None:
                empty_streaming_result = self.metadata_service.build_streaming_result(content="", event=None)
                result = AgentStreamingResult(streaming_result=empty_streaming_result)
            end_event_data = self._finalize_streaming_response(assistant_message, conversation, result)
            yield ("end", end_event_data)

            logger.info(f"Streaming conversation created: {conversation.uuid}")
        finally:
            # Persist buffered tool calls if streaming was interrupted
            if not streaming_completed and tool_call_buffer:
                try:
                    self.tool_call_repo.create_batch(
                        message_id=assistant_message.id,
                        tool_calls=list(tool_call_buffer.values()),
                    )
                    self.session.flush()
                    logger.warning(
                        f"Persisted {len(tool_call_buffer)} tool calls after streaming interruption " f"in conversation {conversation.uuid}"
                    )
                except Exception as e:
                    logger.error(f"Failed to persist tool calls after streaming interruption: {e}")

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
            ConversationNotFoundError: If conversation not found
            ConversationAccessDeniedError: If user doesn't own the conversation
        """
        conversation = self.validate_conversation_access(uuid, user_id)

        self.conversation_repo.delete(conversation)
        logger.info(f"Deleted conversation {uuid}")

    def validate_conversation_access(
        self,
        uuid: str,
        user_id: int,
        *,
        with_messages: bool = False,
    ) -> Conversation:
        """
        Validate that a conversation exists and user has access.

        Args:
            uuid: Conversation UUID
            user_id: User ID
            with_messages: If True, load messages with the conversation

        Returns:
            The validated conversation

        Raises:
            ConversationNotFoundError: If conversation not found
            ConversationAccessDeniedError: If user doesn't own the conversation
        """
        if with_messages:
            conversation = self.conversation_repo.find_by_uuid_with_messages(uuid)
        else:
            conversation = self.conversation_repo.find_by_uuid(uuid)

        if not conversation:
            raise ConversationNotFoundError(uuid)

        if conversation.user_id != user_id:
            raise ConversationAccessDeniedError(uuid)

        return conversation

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
            ConversationNotFoundError: If conversation not found
            ConversationAccessDeniedError: If user doesn't own the conversation
        """
        conversation = self.validate_conversation_access(uuid, user_id, with_messages=True)

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

        # Generate AI response using agent with common event processing
        # Consume streaming generator to get result with metadata (don't yield events)
        tool_call_buffer: dict[str, ToolCallData] = {}
        response_generator = self._stream_agent_response(messages, tool_call_buffer)
        result: AgentStreamingResult | None = None
        try:
            while True:
                next(response_generator)  # Consume events without yielding
        except StopIteration as e:
            result = e.value

        if result is None:
            empty_streaming_result = self.metadata_service.build_streaming_result(content="", event=None)
            result = AgentStreamingResult(streaming_result=empty_streaming_result)

        # Batch insert tool calls and update assistant message
        self.tool_call_repo.create_batch(
            message_id=assistant_message.id,
            tool_calls=result.tool_calls,
        )
        self.metadata_service.apply_streaming_result_to_message(assistant_message, result.streaming_result)

        # Update conversation timestamp
        self.conversation_repo.touch(conversation)

        # Single flush for all database operations
        self.session.flush()

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
    ) -> Generator[StreamingEvent, None, None]:
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
            ConversationNotFoundError: If conversation not found
            ConversationAccessDeniedError: If user doesn't own the conversation
        """
        conversation = self.validate_conversation_access(uuid, user_id, with_messages=True)

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

        # Generate and stream AI response using common method
        # Tool call buffer is passed to allow persistence on abort
        tool_call_buffer: dict[str, ToolCallData] = {}
        response_generator = self._stream_agent_response(messages, tool_call_buffer)
        result: AgentStreamingResult | None = None
        streaming_completed = False
        try:
            try:
                while True:
                    streaming_event = next(response_generator)
                    yield streaming_event
            except StopIteration as e:
                result = e.value
                streaming_completed = True

            # Finalize and yield end event (only on successful completion)
            if result is None:
                empty_streaming_result = self.metadata_service.build_streaming_result(content="", event=None)
                result = AgentStreamingResult(streaming_result=empty_streaming_result)
            end_event_data = self._finalize_streaming_response(assistant_message, conversation, result)
            yield ("end", end_event_data)

            logger.info(f"Streaming message exchange in conversation {uuid}")
        finally:
            # Persist buffered tool calls if streaming was interrupted
            if not streaming_completed and tool_call_buffer:
                try:
                    self.tool_call_repo.create_batch(
                        message_id=assistant_message.id,
                        tool_calls=list(tool_call_buffer.values()),
                    )
                    self.session.flush()
                    logger.warning(f"Persisted {len(tool_call_buffer)} tool calls after streaming interruption " f"in conversation {uuid}")
                except Exception as e:
                    logger.error(f"Failed to persist tool calls after streaming interruption: {e}")

    def _finalize_streaming_response(
        self,
        assistant_message: Message,
        conversation: Conversation,
        result: AgentStreamingResult,
    ) -> dict:
        """
        Finalize streaming response and prepare end event data.

        Performs batch database operations for tool calls, updates the assistant
        message with final content and metadata, touches the conversation timestamp,
        and returns the end event data.

        This method consolidates all database writes into a single flush operation,
        reducing the number of database round-trips during streaming.

        Args:
            assistant_message: The assistant message to update
            conversation: The conversation to touch
            result: The AgentStreamingResult with content, metadata, and tool calls

        Returns:
            Dict containing end event data with metadata
        """
        # Batch insert all tool calls in a single operation
        created_tool_calls = self.tool_call_repo.create_batch(
            message_id=assistant_message.id,
            tool_calls=result.tool_calls,
        )

        # Update assistant message with final content and metadata
        self.metadata_service.apply_streaming_result_to_message(assistant_message, result.streaming_result)

        # Update conversation timestamp
        self.conversation_repo.touch(conversation)

        # Single flush for all database operations
        self.session.flush()

        # Convert created tool calls to response format
        tool_calls_data = [ToolCallResponse.model_validate(tc).model_dump(mode="json") for tc in created_tool_calls]

        # Get metadata as nullable dict
        metadata_dict = self.metadata_service.to_response_dict(result.streaming_result)

        # Build response with explicit field ordering:
        # 1. Message identification
        # 2. Message content
        # 3. Tool calls
        # 4. Metadata (tokens, model, timing, cost)
        return {
            "assistant_message_id": assistant_message.id,
            "content": result.streaming_result.content,
            "tool_calls": tool_calls_data,
            "input_tokens": metadata_dict["input_tokens"],
            "output_tokens": metadata_dict["output_tokens"],
            "model": metadata_dict["model"],
            "response_time_ms": metadata_dict["response_time_ms"],
            "cost_usd": metadata_dict["cost_usd"],
        }

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

    def _process_agent_event(
        self,
        event: AgentEvent,
        tool_call_buffer: dict[str, ToolCallData],
    ) -> tuple[StreamingEvent | None, str | None]:
        """
        Process a single agent event and buffer tool calls for batch insert.

        Instead of writing to the database immediately, tool call data is buffered
        in memory and written in a single batch operation after streaming completes.
        This reduces database round-trips and improves performance.

        Args:
            event: Agent event to process
            tool_call_buffer: Dictionary mapping tool_call_id to ToolCallData
                             (modified in place)

        Returns:
            Tuple of (streaming_event, text_delta):
            - streaming_event: Event tuple to yield, or None if no event to emit
            - text_delta: Text content from the event, or None
        """
        if isinstance(event, ToolCallEvent):
            # Buffer tool call data instead of writing to DB
            tool_call_buffer[event.tool_call_id] = ToolCallData(
                tool_call_id=event.tool_call_id,
                tool_name=event.tool_name,
                input_data=event.input,
            )
            return (
                (
                    "tool_call_start",
                    {
                        "tool_call_id": event.tool_call_id,
                        "tool_name": event.tool_name,
                        "input": event.input,
                    },
                ),
                None,
            )
        elif isinstance(event, ToolResultEvent):
            # Update buffered tool call with result
            if event.tool_call_id in tool_call_buffer:
                tool_call_buffer[event.tool_call_id].complete(
                    output=event.output,
                    error=event.error,
                )
            return (
                (
                    "tool_call_end",
                    {
                        "tool_call_id": event.tool_call_id,
                        "output": event.output,
                        "error": event.error,
                    },
                ),
                None,
            )
        elif isinstance(event, TextDeltaEvent):
            return (("delta", {"delta": event.delta}), event.delta)
        elif isinstance(event, MessageCompleteEvent):
            return (None, event.content)
        elif isinstance(event, RetryEvent):
            return (
                (
                    "retry",
                    {
                        "attempt": event.attempt,
                        "max_attempts": event.max_attempts,
                        "error_type": event.error_type,
                        "delay": event.delay,
                    },
                ),
                None,
            )
        return (None, None)

    def _stream_agent_response(
        self,
        messages: list[dict],
        tool_call_buffer: dict[str, ToolCallData],
    ) -> Generator[StreamingEvent, None, AgentStreamingResult]:
        """
        Stream agent response, yielding events and returning result with metadata.

        Tool calls are buffered in the provided tool_call_buffer during streaming
        and returned as part of the AgentStreamingResult for batch database
        operations after streaming completes. The buffer is modified in place,
        allowing callers to access partial results if streaming is interrupted.

        Args:
            messages: Message history for the agent
            tool_call_buffer: Dictionary to store tool calls (modified in place).
                             Callers should provide an empty dict and can use it
                             in a finally block to persist partial results on abort.

        Yields:
            StreamingEvent tuples for tool calls and text deltas

        Returns:
            AgentStreamingResult with content, metadata, and buffered tool calls
        """
        full_response = ""
        metadata_event: MessageMetadataEvent | None = None

        for event in self.agent_service.generate_response(messages, stream=True):
            streaming_event, text_content = self._process_agent_event(event, tool_call_buffer)
            if streaming_event is not None:
                yield streaming_event
            if text_content is not None:
                if isinstance(event, TextDeltaEvent):
                    full_response += text_content
                elif isinstance(event, MessageCompleteEvent):
                    full_response = text_content

            # Capture metadata event
            if isinstance(event, MessageMetadataEvent):
                metadata_event = event

        # Build streaming result with metadata using MetadataService
        streaming_result = self.metadata_service.build_streaming_result(
            content=full_response,
            event=metadata_event,
        )

        # Return result with buffered tool calls
        return AgentStreamingResult(
            streaming_result=streaming_result,
            tool_calls=list(tool_call_buffer.values()),
        )


__all__ = ["ConversationService"]
