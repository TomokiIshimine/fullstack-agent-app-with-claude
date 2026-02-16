"""User setting repository for database operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from app.models.user_setting import UserSetting
from app.repositories.base import BaseRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

SendShortcutType = Literal["enter", "ctrl_enter"]


class UserSettingRepository(BaseRepository):
    """Repository for UserSetting model database operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session."""
        super().__init__(session)

    def find_by_user_id(self, user_id: int) -> UserSetting | None:
        """
        Find settings by user ID.

        Args:
            user_id: User ID to search for

        Returns:
            UserSetting if found, None otherwise
        """
        return self.session.query(UserSetting).filter(UserSetting.user_id == user_id).first()

    def create(self, user_id: int, send_shortcut: SendShortcutType = "enter") -> UserSetting:
        """
        Create new user settings.

        Args:
            user_id: User ID
            send_shortcut: Send shortcut setting value

        Returns:
            Created UserSetting instance
        """
        setting = UserSetting(user_id=user_id, send_shortcut=send_shortcut)
        self.session.add(setting)
        self.session.flush()
        return setting

    def update(self, setting: UserSetting, *, send_shortcut: SendShortcutType) -> UserSetting:
        """
        Update user settings.

        Args:
            setting: UserSetting instance to update
            send_shortcut: New send shortcut value

        Returns:
            Updated UserSetting instance
        """
        setting.send_shortcut = send_shortcut
        self.session.flush()
        return setting


__all__ = ["UserSettingRepository"]
