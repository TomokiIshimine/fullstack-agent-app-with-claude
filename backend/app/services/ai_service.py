"""AI service for Claude API integration."""

from __future__ import annotations

import logging
import os
from typing import Generator

from anthropic import Anthropic

logger = logging.getLogger(__name__)

# System prompt for the AI assistant
SYSTEM_PROMPT = """You are a helpful AI assistant. Please respond in the same language as the user."""


class AIService:
    """Service for AI-powered chat functionality using Claude API."""

    def __init__(self):
        """Initialize AI service with Claude client."""
        self.client = Anthropic()
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250514")
        self.max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))
        self.system_prompt = SYSTEM_PROMPT

    def generate_response(
        self,
        messages: list[dict],
        stream: bool = True,
    ) -> Generator[str, None, None] | str:
        """
        Generate AI response for a conversation.

        Args:
            messages: Conversation history as list of dicts with 'role' and 'content'
            stream: Whether to stream the response

        Returns:
            If stream=True: Generator yielding text chunks
            If stream=False: Complete response text
        """
        logger.debug(f"Generating AI response with {len(messages)} messages, stream={stream}")

        if stream:
            return self._stream_response(messages)
        else:
            return self._sync_response(messages)

    def _stream_response(self, messages: list[dict]) -> Generator[str, None, None]:
        """
        Generate streaming AI response.

        Args:
            messages: Conversation history

        Yields:
            Text chunks as they become available
        """
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Error streaming AI response: {e}")
            raise

    def _sync_response(self, messages: list[dict]) -> str:
        """
        Generate non-streaming AI response.

        Args:
            messages: Conversation history

        Returns:
            Complete response text
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages=messages,
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            raise

    def generate_title(self, first_message: str) -> str:
        """
        Generate a title for a conversation based on the first message.

        Args:
            first_message: The first user message in the conversation

        Returns:
            Generated title (max 50 characters)
        """
        # Simple approach: truncate the first message
        title = first_message.strip()
        if len(title) > 50:
            title = title[:47] + "..."
        return title


__all__ = ["AIService", "SYSTEM_PROMPT"]
