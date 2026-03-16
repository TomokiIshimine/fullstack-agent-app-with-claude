"""Suggestion service for generating reply suggestions using Claude API."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, cast

import anthropic

from app.constants.suggestion import (
    SUGGESTION_MAX_TOKENS,
    SUGGESTION_MESSAGE_LIMIT,
    SUGGESTION_MODEL,
    SUGGESTION_SYSTEM_PROMPT,
    SUGGESTION_TOOL_DEFINITION,
    SUGGESTION_TOOL_NAME,
)
from app.core.exceptions import ConversationAccessDeniedError, ConversationNotFoundError
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.suggestion import SuggestionsResponse

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SuggestionService:
    """Service for generating reply suggestions using Claude Haiku."""

    def __init__(self, session: Session, client: anthropic.Anthropic | None = None) -> None:
        """Initialize service with database session and optional Anthropic client.

        Args:
            session: SQLAlchemy database session.
            client: Anthropic client instance. If None, creates one from environment.
        """
        self.session = session
        self.conversation_repo = ConversationRepository(session)
        self.message_repo = MessageRepository(session)
        self._client = client

    @property
    def client(self) -> anthropic.Anthropic:
        """Get Anthropic client, creating lazily if needed."""
        if self._client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def generate_suggestions(self, uuid: str, user_id: int) -> SuggestionsResponse:
        """Generate reply suggestions for a conversation.

        Args:
            uuid: Conversation UUID.
            user_id: ID of the requesting user.

        Returns:
            SuggestionsResponse with generated suggestions.

        Raises:
            ConversationNotFoundError: If conversation not found.
            ConversationAccessDeniedError: If user doesn't own the conversation.
        """
        # Validate conversation access
        conversation = self.conversation_repo.find_by_uuid(uuid)
        if conversation is None:
            raise ConversationNotFoundError(uuid=uuid)
        if conversation.user_id != user_id:
            raise ConversationAccessDeniedError(uuid=uuid)

        # Get recent messages
        all_messages = self.message_repo.find_by_conversation_id(conversation.id)
        recent_messages = list(all_messages[-SUGGESTION_MESSAGE_LIMIT:])

        if not recent_messages:
            return SuggestionsResponse(suggestions=[])

        # Build messages for Claude API
        api_messages: list[dict[str, Any]] = [{"role": msg.role, "content": msg.content} for msg in recent_messages]

        # Call Claude API with Tool Use for structured output
        try:
            response = self.client.messages.create(
                model=SUGGESTION_MODEL,
                max_tokens=SUGGESTION_MAX_TOKENS,
                system=SUGGESTION_SYSTEM_PROMPT,
                messages=cast(Any, api_messages),
                tools=cast(Any, [SUGGESTION_TOOL_DEFINITION]),
                tool_choice=cast(Any, {"type": "tool", "name": SUGGESTION_TOOL_NAME}),
            )

            # Extract suggestions from tool use response
            for block in response.content:
                if block.type == "tool_use" and block.name == SUGGESTION_TOOL_NAME:
                    suggestions = cast(list[str], block.input.get("suggestions", []))
                    return SuggestionsResponse(suggestions=suggestions)

            # No tool use block found
            logger.warning("No tool_use block found in suggestion response")
            return SuggestionsResponse(suggestions=[])

        except Exception:
            logger.error("Failed to generate suggestions", exc_info=True)
            return SuggestionsResponse(suggestions=[])


__all__ = ["SuggestionService"]
