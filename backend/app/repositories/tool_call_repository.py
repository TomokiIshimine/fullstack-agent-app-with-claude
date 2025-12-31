"""ToolCall repository for database operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Literal, Sequence

from app.models.tool_call import ToolCall
from app.repositories.base import BaseRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@dataclass
class ToolCallData:
    """Data class for buffering tool call information before batch insert.

    This class holds tool call data in memory during streaming,
    allowing batch database operations after streaming completes.
    """

    tool_call_id: str
    tool_name: str
    input_data: dict[str, Any]
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    output: str | None = None
    error: str | None = None
    status: Literal["pending", "success", "error"] = "pending"
    completed_at: datetime | None = None

    def complete(
        self,
        output: str | None = None,
        error: str | None = None,
    ) -> None:
        """Mark tool call as completed with result.

        Args:
            output: Tool execution output (if successful)
            error: Error message (if failed)
        """
        self.output = output
        self.error = error
        self.status = "error" if error else "success"
        self.completed_at = datetime.now(timezone.utc)


class ToolCallRepository(BaseRepository):
    """Repository for ToolCall model database operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session."""
        super().__init__(session)

    def find_by_message_id(self, message_id: int) -> Sequence[ToolCall]:
        """
        Find all tool calls for a message ordered by start time.

        Args:
            message_id: Message ID to filter by

        Returns:
            Sequence of ToolCall instances
        """
        return self.session.query(ToolCall).filter(ToolCall.message_id == message_id).order_by(ToolCall.started_at.asc()).all()

    def create(
        self,
        message_id: int,
        tool_call_id: str,
        tool_name: str,
        input_data: dict[str, Any],
    ) -> ToolCall:
        """
        Create a new tool call record (pending status).

        Args:
            message_id: Parent message ID
            tool_call_id: Unique tool call ID from LangGraph
            tool_name: Name of the tool being called
            input_data: Input arguments for the tool

        Returns:
            Created ToolCall instance
        """
        tool_call = ToolCall(
            message_id=message_id,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            input=input_data,
            status="pending",
        )
        self.session.add(tool_call)
        self.session.flush()
        return tool_call

    def update_completed(
        self,
        tool_call_id: str,
        output: str | None,
        error: str | None,
        status: Literal["success", "error"],
    ) -> ToolCall | None:
        """
        Update a tool call with completion data.

        Args:
            tool_call_id: Unique tool call ID
            output: Tool execution output (if successful)
            error: Error message (if failed)
            status: Final status ('success' or 'error')

        Returns:
            Updated ToolCall instance, or None if not found
        """
        tool_call = self.session.query(ToolCall).filter(ToolCall.tool_call_id == tool_call_id).first()
        if tool_call:
            tool_call.output = output
            tool_call.error = error
            tool_call.status = status
            tool_call.completed_at = datetime.now(timezone.utc)
            self.session.flush()
        return tool_call

    def create_batch(
        self,
        message_id: int,
        tool_calls: Sequence[ToolCallData],
    ) -> list[ToolCall]:
        """
        Create multiple tool call records in a single batch operation.

        This method is optimized for streaming scenarios where tool calls
        are buffered in memory and written to the database after streaming
        completes. This reduces the number of database round-trips and
        improves performance.

        Args:
            message_id: Parent message ID for all tool calls
            tool_calls: Sequence of ToolCallData instances to persist

        Returns:
            List of created ToolCall instances
        """
        if not tool_calls:
            return []

        created_tool_calls = []
        for data in tool_calls:
            tool_call = ToolCall(
                message_id=message_id,
                tool_call_id=data.tool_call_id,
                tool_name=data.tool_name,
                input=data.input_data,
                output=data.output,
                error=data.error,
                status=data.status,
                started_at=data.started_at,
                completed_at=data.completed_at,
            )
            self.session.add(tool_call)
            created_tool_calls.append(tool_call)

        # Single flush for all tool calls
        self.session.flush()
        return created_tool_calls


__all__ = ["ToolCallRepository", "ToolCallData"]
