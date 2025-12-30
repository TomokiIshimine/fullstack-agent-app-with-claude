"""Admin conversation service for viewing all users' conversations."""

from __future__ import annotations

import logging
import math

from sqlalchemy.orm import Session

from app.constants.pagination import DEFAULT_PER_PAGE, MAX_PER_PAGE, MIN_PER_PAGE
from app.core.exceptions import ConversationNotFoundError
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin_conversation import AdminConversationDetailResponse, AdminConversationListResponse, AdminConversationResponse, AdminUserInfo
from app.schemas.conversation import MessageResponse, PaginationMeta

logger = logging.getLogger(__name__)


class AdminConversationService:
    """Service for admin conversation operations."""

    def __init__(self, session: Session):
        """Initialize service with database session.

        Args:
            session: SQLAlchemy database session.
        """
        self.session = session
        self.conversation_repo = ConversationRepository(session)
        self.user_repo = UserRepository(session)

    def list_all_conversations(
        self,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE,
        user_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> AdminConversationListResponse:
        """
        List all conversations for admin with optional filters.

        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            user_id: Optional filter by user ID
            start_date: Optional filter by start date (ISO format)
            end_date: Optional filter by end date (ISO format)

        Returns:
            AdminConversationListResponse with conversations and pagination meta
        """
        # Clamp per_page to reasonable limits
        per_page = max(MIN_PER_PAGE, min(per_page, MAX_PER_PAGE))
        page = max(1, page)

        conversations_data, total = self.conversation_repo.find_all_with_user(
            page=page,
            per_page=per_page,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        total_pages = math.ceil(total / per_page) if total > 0 else 1

        conversations = [
            AdminConversationResponse(
                uuid=item["conversation"].uuid,
                title=item["conversation"].title,
                message_count=item["message_count"],
                user=AdminUserInfo(
                    id=item["user"].id,
                    email=item["user"].email,
                    name=item["user"].name,
                ),
                created_at=item["conversation"].created_at,
                updated_at=item["conversation"].updated_at,
            )
            for item in conversations_data
        ]

        logger.info(
            "Admin listing conversations",
            extra={
                "total": total,
                "page": page,
                "user_id_filter": user_id,
                "start_date_filter": start_date,
                "end_date_filter": end_date,
            },
        )

        return AdminConversationListResponse(
            conversations=conversations,
            meta=PaginationMeta(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
            ),
        )

    def get_conversation_detail(self, uuid: str) -> AdminConversationDetailResponse:
        """
        Get a conversation with all messages for admin view.

        Args:
            uuid: Conversation UUID

        Returns:
            AdminConversationDetailResponse with conversation and messages

        Raises:
            ConversationNotFoundError: If conversation not found
        """
        conversation = self.conversation_repo.find_by_uuid_with_messages(uuid)

        if not conversation:
            raise ConversationNotFoundError(uuid)

        user = self.user_repo.find_by_id(conversation.user_id)

        if not user:
            raise ConversationNotFoundError(uuid)

        logger.info(
            "Admin viewing conversation detail",
            extra={"conversation_uuid": uuid, "user_id": conversation.user_id},
        )

        return AdminConversationDetailResponse(
            uuid=conversation.uuid,
            title=conversation.title,
            user=AdminUserInfo(
                id=user.id,
                email=user.email,
                name=user.name,
            ),
            messages=[MessageResponse.model_validate(msg) for msg in conversation.messages],
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )


__all__ = ["AdminConversationService"]
