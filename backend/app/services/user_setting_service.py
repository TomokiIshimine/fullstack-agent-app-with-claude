"""User setting management service."""

from __future__ import annotations

import logging
from typing import Literal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.user_setting_repository import UserSettingRepository

SendShortcutType = Literal["enter", "ctrl_enter"]

logger = logging.getLogger(__name__)

# Default setting values (used when no DB record exists)
DEFAULT_SEND_SHORTCUT = "enter"


class UserSettingService:
    """Service for user setting operations."""

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.setting_repo = UserSettingRepository(session)

    def get_settings(self, user_id: int) -> dict:
        """
        Get user settings. Returns defaults if no record exists.

        Args:
            user_id: ID of the user

        Returns:
            Dict with setting values
        """
        setting = self.setting_repo.find_by_user_id(user_id)

        if setting:
            return {"send_shortcut": setting.send_shortcut}

        logger.debug(f"No settings found for user_id={user_id}, returning defaults")
        return {"send_shortcut": DEFAULT_SEND_SHORTCUT}

    def update_settings(self, user_id: int, send_shortcut: SendShortcutType) -> dict:
        """
        Update user settings (upsert: create if not exists, update if exists).

        Handles race conditions where concurrent requests may both attempt to
        insert a new record by catching IntegrityError and retrying as update.

        Args:
            user_id: ID of the user
            send_shortcut: New send shortcut value

        Returns:
            Dict with updated setting values
        """
        setting = self.setting_repo.find_by_user_id(user_id)

        if setting:
            self.setting_repo.update(setting, send_shortcut=send_shortcut)
            logger.info(f"User settings updated: user_id={user_id}, " f"send_shortcut={send_shortcut}")
        else:
            try:
                self.setting_repo.create(user_id=user_id, send_shortcut=send_shortcut)
                logger.info(f"User settings created: user_id={user_id}, " f"send_shortcut={send_shortcut}")
            except IntegrityError:
                # Concurrent insert race: rollback and retry as update
                self.session.rollback()
                setting = self.setting_repo.find_by_user_id(user_id)
                if setting:
                    self.setting_repo.update(setting, send_shortcut=send_shortcut)
                    logger.info(f"User settings updated (retry after conflict): user_id={user_id}, " f"send_shortcut={send_shortcut}")

        return {"send_shortcut": send_shortcut}


__all__ = ["UserSettingService"]
