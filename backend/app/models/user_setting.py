from __future__ import annotations

from datetime import datetime
from typing import Literal

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class UserSetting(Base):
    """User settings model for per-user preferences."""

    __tablename__ = "user_settings"
    __table_args__ = ({"sqlite_autoincrement": True},)

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    send_shortcut: Mapped[Literal["enter", "ctrl_enter"]] = mapped_column(
        Enum("enter", "ctrl_enter", name="send_shortcut_type"),
        nullable=False,
        server_default="enter",
    )
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
    user: Mapped["User"] = relationship("User", back_populates="settings")  # type: ignore  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"UserSetting(id={self.id!r}, user_id={self.user_id!r}, send_shortcut={self.send_shortcut!r})"


__all__ = ["UserSetting"]
