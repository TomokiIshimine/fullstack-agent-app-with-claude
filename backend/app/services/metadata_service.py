"""Metadata service for message metadata processing."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.services.agent_service import MessageMetadataEvent
from app.utils.cost_calculator import calculate_cost

if TYPE_CHECKING:
    from app.models.message import Message

logger = logging.getLogger(__name__)


@dataclass
class StreamingResult:
    """Result from streaming agent response with metadata."""

    content: str
    input_tokens: int
    output_tokens: int
    model: str
    response_time_ms: int
    cost_usd: float


@dataclass
class MessageMetadata:
    """Message metadata container."""

    input_tokens: int
    output_tokens: int
    model: str
    response_time_ms: int
    cost_usd: float

    @classmethod
    def empty(cls) -> MessageMetadata:
        """Create an empty metadata instance."""
        return cls(
            input_tokens=0,
            output_tokens=0,
            model="",
            response_time_ms=0,
            cost_usd=0.0,
        )

    def has_data(self) -> bool:
        """Check if metadata has meaningful data."""
        return self.input_tokens > 0 or self.output_tokens > 0 or self.response_time_ms > 0 or self.cost_usd > 0


class MetadataService:
    """Service for message metadata processing.

    Centralizes metadata-related operations:
    - Building metadata from agent events
    - Calculating costs
    - Applying metadata to message models
    - Generating response dictionaries
    """

    def build_from_event(self, event: MessageMetadataEvent | None) -> MessageMetadata:
        """Build metadata from an agent event.

        Args:
            event: MessageMetadataEvent from agent service, or None

        Returns:
            MessageMetadata with calculated cost
        """
        if event is None:
            return MessageMetadata.empty()

        cost_usd = 0.0
        if event.input_tokens > 0:
            cost_usd = calculate_cost(
                model=event.model,
                input_tokens=event.input_tokens,
                output_tokens=event.output_tokens,
            )

        return MessageMetadata(
            input_tokens=event.input_tokens,
            output_tokens=event.output_tokens,
            model=event.model,
            response_time_ms=event.response_time_ms,
            cost_usd=cost_usd,
        )

    def build_streaming_result(
        self,
        content: str,
        event: MessageMetadataEvent | None,
    ) -> StreamingResult:
        """Build a streaming result with metadata.

        Args:
            content: Response content
            event: MessageMetadataEvent from agent service, or None

        Returns:
            StreamingResult with content and metadata
        """
        metadata = self.build_from_event(event)
        return StreamingResult(
            content=content,
            input_tokens=metadata.input_tokens,
            output_tokens=metadata.output_tokens,
            model=metadata.model,
            response_time_ms=metadata.response_time_ms,
            cost_usd=metadata.cost_usd,
        )

    def apply_to_message(self, message: Message, metadata: MessageMetadata) -> None:
        """Apply metadata to a message model.

        Sets metadata fields on the message, using None for zero/empty values
        to avoid clutter in the database.

        Args:
            message: Message model to update
            metadata: Metadata to apply
        """
        message.input_tokens = metadata.input_tokens if metadata.input_tokens > 0 else None
        message.output_tokens = metadata.output_tokens if metadata.output_tokens > 0 else None
        message.model = metadata.model if metadata.model else None
        message.response_time_ms = metadata.response_time_ms if metadata.response_time_ms > 0 else None
        message.cost_usd = metadata.cost_usd if metadata.cost_usd > 0 else None

    def apply_streaming_result_to_message(
        self,
        message: Message,
        result: StreamingResult,
    ) -> None:
        """Apply streaming result metadata to a message model.

        Args:
            message: Message model to update
            result: StreamingResult containing metadata
        """
        message.content = result.content
        message.input_tokens = result.input_tokens if result.input_tokens > 0 else None
        message.output_tokens = result.output_tokens if result.output_tokens > 0 else None
        message.model = result.model if result.model else None
        message.response_time_ms = result.response_time_ms if result.response_time_ms > 0 else None
        message.cost_usd = result.cost_usd if result.cost_usd > 0 else None

    def to_response_dict(self, result: StreamingResult) -> dict:
        """Convert streaming result metadata to response dictionary.

        Returns metadata fields for API responses, using None for zero/empty values.

        Args:
            result: StreamingResult containing metadata

        Returns:
            Dict with metadata fields for API response
        """
        return {
            "input_tokens": result.input_tokens if result.input_tokens > 0 else None,
            "output_tokens": result.output_tokens if result.output_tokens > 0 else None,
            "model": result.model if result.model else None,
            "response_time_ms": result.response_time_ms if result.response_time_ms > 0 else None,
            "cost_usd": result.cost_usd if result.cost_usd > 0 else None,
        }


__all__ = ["MetadataService", "StreamingResult", "MessageMetadata"]
