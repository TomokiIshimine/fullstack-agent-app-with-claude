"""Conversation model for chat functionality."""

from __future__ import annotations

import uuid as uuid_module
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if TYPE_CHECKING:
    from .message import Message
    from .user import User


class Conversation(Base):
    """Conversation model for storing chat threads."""

    __tablename__ = "conversations"
    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_updated_at", "updated_at"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    uuid: Mapped[str] = mapped_column(
        String(length=36),
        nullable=False,
        unique=True,
        default=lambda: str(uuid_module.uuid4()),
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(length=255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Conversation(id={self.id!r}, uuid={self.uuid!r}, title={self.title!r})"


__all__ = ["Conversation"]
