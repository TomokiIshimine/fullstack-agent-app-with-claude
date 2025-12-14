"""Conversation repository for database operations."""

from __future__ import annotations

import uuid as uuid_module
from typing import Sequence

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:
    """Repository for Conversation model database operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def find_by_uuid(self, uuid: str) -> Conversation | None:
        """
        Find a conversation by UUID.

        Args:
            uuid: UUID to search for

        Returns:
            Conversation if found, None otherwise
        """
        return self.session.query(Conversation).filter(Conversation.uuid == uuid).first()

    def find_by_uuid_with_messages(self, uuid: str) -> Conversation | None:
        """
        Find a conversation by UUID with messages eagerly loaded.

        Args:
            uuid: UUID to search for

        Returns:
            Conversation with messages if found, None otherwise
        """
        return self.session.query(Conversation).options(joinedload(Conversation.messages)).filter(Conversation.uuid == uuid).first()

    def find_by_user_id(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[Sequence[Conversation], int]:
        """
        Find all conversations for a user with pagination.

        Args:
            user_id: User ID to filter by
            page: Page number (1-indexed)
            per_page: Number of items per page

        Returns:
            Tuple of (conversations list, total count)
        """
        query = self.session.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc())

        total = query.count()
        offset = (page - 1) * per_page
        conversations = query.offset(offset).limit(per_page).all()

        return conversations, total

    def find_by_user_id_with_message_count(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict], int]:
        """
        Find all conversations for a user with message counts.

        Args:
            user_id: User ID to filter by
            page: Page number (1-indexed)
            per_page: Number of items per page

        Returns:
            Tuple of (list of dicts with conversation and message_count, total count)
        """
        # Subquery to count messages per conversation
        message_count_subquery = (
            self.session.query(
                Message.conversation_id,
                func.count(Message.id).label("message_count"),
            )
            .group_by(Message.conversation_id)
            .subquery()
        )

        query = (
            self.session.query(
                Conversation,
                func.coalesce(message_count_subquery.c.message_count, 0).label("message_count"),
            )
            .outerjoin(
                message_count_subquery,
                Conversation.id == message_count_subquery.c.conversation_id,
            )
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )

        # Get total count
        total = self.session.query(Conversation).filter(Conversation.user_id == user_id).count()

        offset = (page - 1) * per_page
        results = query.offset(offset).limit(per_page).all()

        conversations_with_count = [{"conversation": conv, "message_count": count} for conv, count in results]

        return conversations_with_count, total

    def create(self, user_id: int, title: str) -> Conversation:
        """
        Create a new conversation.

        Args:
            user_id: Owner user ID
            title: Conversation title

        Returns:
            Created Conversation instance
        """
        conversation = Conversation(
            uuid=str(uuid_module.uuid4()),
            user_id=user_id,
            title=title,
        )
        self.session.add(conversation)
        self.session.flush()
        return conversation

    def update_title(self, conversation: Conversation, title: str) -> Conversation:
        """
        Update conversation title.

        Args:
            conversation: Conversation to update
            title: New title

        Returns:
            Updated Conversation instance
        """
        conversation.title = title
        return conversation

    def touch(self, conversation: Conversation) -> Conversation:
        """
        Update conversation's updated_at timestamp.

        Args:
            conversation: Conversation to touch

        Returns:
            Updated Conversation instance
        """
        conversation.updated_at = func.now()
        return conversation

    def delete(self, conversation: Conversation) -> None:
        """
        Delete a conversation.

        Args:
            conversation: Conversation to delete
        """
        self.session.delete(conversation)


__all__ = ["ConversationRepository"]
