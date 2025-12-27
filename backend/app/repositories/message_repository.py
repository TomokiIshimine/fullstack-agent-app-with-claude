"""Message repository for database operations."""

from __future__ import annotations

from typing import Literal, Sequence

from sqlalchemy.orm import Session

from app.models.message import Message


class MessageRepository:
    """Repository for Message model database operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

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
    ) -> Message:
        """
        Create a new message.

        Args:
            conversation_id: Parent conversation ID
            role: Message role ('user' or 'assistant')
            content: Message content

        Returns:
            Created Message instance
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self.session.add(message)
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
