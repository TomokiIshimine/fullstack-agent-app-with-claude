"""Message repository for database operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Sequence

from app.models.message import Message
from app.repositories.base import BaseRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class MessageRepository(BaseRepository):
    """Repository for Message model database operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session."""
        super().__init__(session)

    def find_by_conversation_id(self, conversation_id: int) -> Sequence[Message]:
        """
        Find all messages for a conversation ordered by creation time.

        Args:
            conversation_id: Conversation ID to filter by

        Returns:
            Sequence of Message instances
        """
        return self.session.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()

    def create(
        self,
        conversation_id: int,
        role: Literal["user", "assistant"],
        content: str,
        *,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        model: str | None = None,
        response_time_ms: int | None = None,
        cost_usd: float | None = None,
    ) -> Message:
        """
        Create a new message.

        Args:
            conversation_id: Parent conversation ID
            role: Message role ('user' or 'assistant')
            content: Message content
            input_tokens: Number of input tokens (for assistant messages)
            output_tokens: Number of output tokens (for assistant messages)
            model: Model name used (for assistant messages)
            response_time_ms: Response time in milliseconds (for assistant messages)
            cost_usd: Cost in USD (for assistant messages)

        Returns:
            Created Message instance
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            response_time_ms=response_time_ms,
            cost_usd=cost_usd,
        )
        self.session.add(message)
        self.session.flush()
        return message

    def update_metadata(
        self,
        message_id: int,
        *,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        model: str | None = None,
        response_time_ms: int | None = None,
        cost_usd: float | None = None,
    ) -> Message | None:
        """
        Update message metadata.

        Args:
            message_id: Message ID to update
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name used
            response_time_ms: Response time in milliseconds
            cost_usd: Cost in USD

        Returns:
            Updated Message instance or None if not found
        """
        message = self.session.query(Message).filter(Message.id == message_id).first()
        if message is None:
            return None

        if input_tokens is not None:
            message.input_tokens = input_tokens
        if output_tokens is not None:
            message.output_tokens = output_tokens
        if model is not None:
            message.model = model
        if response_time_ms is not None:
            message.response_time_ms = response_time_ms
        if cost_usd is not None:
            message.cost_usd = cost_usd

        self.session.flush()
        return message

    def count_by_conversation_id(self, conversation_id: int) -> int:
        """
        Count messages in a conversation.

        Args:
            conversation_id: Conversation ID to count messages for

        Returns:
            Number of messages
        """
        return self.session.query(Message).filter(Message.conversation_id == conversation_id).count()

    def delete_by_conversation_id(self, conversation_id: int) -> int:
        """
        Delete all messages for a conversation.

        Args:
            conversation_id: Conversation ID to delete messages for

        Returns:
            Number of messages deleted
        """
        return self.session.query(Message).filter(Message.conversation_id == conversation_id).delete(synchronize_session=False)


__all__ = ["MessageRepository"]
