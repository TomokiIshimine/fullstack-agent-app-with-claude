"""ToolCall model for tracking agent tool usage."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if TYPE_CHECKING:
    from .message import Message


class ToolCall(Base):
    """ToolCall model for storing individual tool invocations."""

    __tablename__ = "tool_calls"
    __table_args__ = (
        Index("idx_tool_calls_message_id", "message_id"),
        Index("idx_tool_calls_tool_call_id", "tool_call_id"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    message_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_call_id: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[Literal["pending", "success", "error"]] = mapped_column(
        Enum("pending", "success", "error", name="tool_call_status"),
        nullable=False,
        default="pending",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="tool_calls")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"ToolCall(id={self.id!r}, tool_name={self.tool_name!r}, status={self.status!r})"


__all__ = ["ToolCall"]
