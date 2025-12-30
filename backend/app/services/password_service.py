"""Password management service for changing passwords."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.exceptions import InvalidPasswordError
from app.repositories.user_repository import UserRepository
from app.utils.password import hash_password, verify_password

logger = logging.getLogger(__name__)


class PasswordService:
    """Service for password management operations."""

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.user_repo = UserRepository(session)

    def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        """
        Change user's password.

        Args:
            user_id: ID of the user
            current_password: Current password for verification
            new_password: New password to set

        Raises:
            InvalidPasswordError: If current password is incorrect
            PasswordChangeFailedError: If password change fails
        """
        # Get user
        user = self.user_repo.find_by_id(user_id)
        if not user:
            logger.warning(f"Password change failed: user not found - id={user_id}")
            # Don't reveal whether user exists - use same error as invalid password
            raise InvalidPasswordError()

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            logger.warning(f"Password change failed: invalid current password - user_id={user_id}")
            raise InvalidPasswordError()

        # Hash new password
        new_password_hash = hash_password(new_password)

        # Update password (session commit/rollback handled by request hooks)
        user.password_hash = new_password_hash
        self.session.flush()

        logger.info(f"Password changed successfully: user_id={user_id}, email={user.email}")


__all__ = ["PasswordService"]
