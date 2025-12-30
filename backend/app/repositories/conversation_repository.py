"""Conversation repository for database operations."""

from __future__ import annotations

import uuid as uuid_module
from typing import TYPE_CHECKING, Sequence

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.constants.pagination import DEFAULT_PER_PAGE
from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.base import BaseRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ConversationRepository(BaseRepository):
    """Repository for Conversation model database operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session."""
        super().__init__(session)

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
        per_page: int = DEFAULT_PER_PAGE,
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

    def find_all_by_user_id(self, user_id: int) -> Sequence[Conversation]:
        """
        Find all conversations for a user.

        Args:
            user_id: User ID to filter by

        Returns:
            Sequence of Conversation instances
        """
        return self.session.query(Conversation).filter(Conversation.user_id == user_id).all()

    def find_by_user_id_with_message_count(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE,
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

    def _build_date_filters(
        self,
        start_date: str | None,
        end_date: str | None,
    ) -> list:
        """Build date filter conditions for queries.

        Args:
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)

        Returns:
            List of SQLAlchemy filter conditions
        """
        from app.utils.date_filter import parse_date_filter

        filters = []
        if start_date:
            start_dt = parse_date_filter(start_date, end_of_day=False)
            if start_dt:
                filters.append(Conversation.created_at >= start_dt)

        if end_date:
            end_dt = parse_date_filter(end_date, end_of_day=True)
            if end_dt:
                filters.append(Conversation.created_at <= end_dt)

        return filters

    def find_all_with_user(
        self,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE,
        user_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> tuple[list[dict], int]:
        """
        Find all conversations with user info for admin view.

        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page
            user_id: Optional user ID filter
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)

        Returns:
            Tuple of (list of dicts with conversation, user, message_count, total count)
        """
        from app.models.user import User

        # Build filter conditions once
        filter_conditions = []
        if user_id is not None:
            filter_conditions.append(Conversation.user_id == user_id)
        filter_conditions.extend(self._build_date_filters(start_date, end_date))

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
                User,
                func.coalesce(message_count_subquery.c.message_count, 0).label("message_count"),
            )
            .join(User, Conversation.user_id == User.id)
            .outerjoin(
                message_count_subquery,
                Conversation.id == message_count_subquery.c.conversation_id,
            )
        )

        # Apply all filters
        for condition in filter_conditions:
            query = query.filter(condition)

        query = query.order_by(Conversation.updated_at.desc())

        # Count total with same filters
        count_query = self.session.query(Conversation)
        for condition in filter_conditions:
            count_query = count_query.filter(condition)
        total = count_query.count()

        offset = (page - 1) * per_page
        results = query.offset(offset).limit(per_page).all()

        conversations_with_user = [
            {
                "conversation": conv,
                "user": user,
                "message_count": count,
            }
            for conv, user, count in results
        ]

        return conversations_with_user, total


__all__ = ["ConversationRepository"]
