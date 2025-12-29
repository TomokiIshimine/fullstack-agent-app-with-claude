"""Tool call request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class ToolCallResponse(BaseModel):
    """Response schema for a tool call."""

    id: int
    tool_call_id: str
    tool_name: str
    input: dict[str, Any]
    output: str | None = None
    error: str | None = None
    status: Literal["pending", "success", "error"]
    started_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ToolCallStartEvent(BaseModel):
    """SSE event data for tool_call_start."""

    tool_call_id: str
    tool_name: str
    input: dict[str, Any]


class ToolCallEndEvent(BaseModel):
    """SSE event data for tool_call_end."""

    tool_call_id: str
    output: str | None = None
    error: str | None = None


__all__ = [
    "ToolCallResponse",
    "ToolCallStartEvent",
    "ToolCallEndEvent",
]
