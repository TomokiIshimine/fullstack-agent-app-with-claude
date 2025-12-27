"""ToolCall repository for database operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Sequence

from sqlalchemy.orm import Session

from app.models.tool_call import ToolCall


class ToolCallRepository:
    """Repository for ToolCall model database operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def find_by_message_id(self, message_id: int) -> Sequence[ToolCall]:
        """
        Find all tool calls for a message ordered by start time.

        Args:
            message_id: Message ID to filter by

        Returns:
            Sequence of ToolCall instances
        """
        return (
            self.session.query(ToolCall)
            .filter(ToolCall.message_id == message_id)
            .order_by(ToolCall.started_at.asc())
            .all()
        )

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
        tool_call = (
            self.session.query(ToolCall)
            .filter(ToolCall.tool_call_id == tool_call_id)
            .first()
        )
        if tool_call:
            tool_call.output = output
            tool_call.error = error
            tool_call.status = status
            tool_call.completed_at = datetime.utcnow()
            self.session.flush()
        return tool_call


__all__ = ["ToolCallRepository"]
