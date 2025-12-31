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

    def to_metadata(self) -> MessageMetadata:
        """Convert to MessageMetadata instance."""
        return MessageMetadata(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            model=self.model,
            response_time_ms=self.response_time_ms,
            cost_usd=self.cost_usd,
        )


@dataclass
class MessageMetadata:
    """Message metadata container (data-only, no business logic)."""

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


class MetadataService:
    """Service for message metadata processing.

    Centralizes all metadata-related operations:
    - Building metadata from agent events
    - Calculating costs
    - Validating metadata (has_valid_data)
    - Converting to nullable dict (to_nullable_dict)
    - Applying metadata to message models
    - Generating response dictionaries
    """

    def has_valid_data(self, metadata: MessageMetadata) -> bool:
        """Check if metadata has meaningful data.

        Args:
            metadata: MessageMetadata to check

        Returns:
            True if metadata contains at least one non-zero/non-empty value
        """
        return metadata.input_tokens > 0 or metadata.output_tokens > 0 or metadata.response_time_ms > 0 or metadata.cost_usd > 0

    def to_nullable_dict(self, metadata: MessageMetadata) -> dict:
        """Convert metadata to dict with None for zero/empty values.

        This is used for both API responses and database storage,
        where we want to avoid storing meaningless zero values.

        Args:
            metadata: MessageMetadata to convert

        Returns:
            Dict with metadata fields, using None for zero/empty values
        """
        return {
            "input_tokens": metadata.input_tokens if metadata.input_tokens > 0 else None,
            "output_tokens": metadata.output_tokens if metadata.output_tokens > 0 else None,
            "model": metadata.model if metadata.model else None,
            "response_time_ms": metadata.response_time_ms if metadata.response_time_ms > 0 else None,
            "cost_usd": metadata.cost_usd if metadata.cost_usd > 0 else None,
        }

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
        nullable = self.to_nullable_dict(metadata)
        message.input_tokens = nullable["input_tokens"]
        message.output_tokens = nullable["output_tokens"]
        message.model = nullable["model"]
        message.response_time_ms = nullable["response_time_ms"]
        message.cost_usd = nullable["cost_usd"]

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
        self.apply_to_message(message, result.to_metadata())

    def to_response_dict(self, result: StreamingResult) -> dict:
        """Convert streaming result metadata to response dictionary.

        Returns metadata fields for API responses, using None for zero/empty values.

        Args:
            result: StreamingResult containing metadata

        Returns:
            Dict with metadata fields for API response
        """
        return self.to_nullable_dict(result.to_metadata())


__all__ = ["MetadataService", "StreamingResult", "MessageMetadata"]
