"""Base repository with common session management logic."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.base import Base

T = TypeVar("T", bound="Base")


class BaseRepository(ABC):
    """Abstract base class for all repositories.

    Provides common session management patterns and helper methods
    for database operations. All repositories should inherit from
    this class.

    Attributes:
        session: SQLAlchemy database session for queries and transactions.
    """

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations.
        """
        self.session = session

    def _add(self, entity: T) -> T:
        """Add an entity to the session.

        Args:
            entity: Model instance to add.

        Returns:
            The added entity.
        """
        self.session.add(entity)
        return entity

    def _add_and_flush(self, entity: T) -> T:
        """Add an entity to the session and flush to get generated values.

        Use this method when you need the entity's generated fields
        (like auto-increment IDs) immediately after creation.

        Args:
            entity: Model instance to add.

        Returns:
            The added entity with generated values populated.
        """
        self.session.add(entity)
        self.session.flush()
        return entity

    def _flush(self) -> None:
        """Flush pending changes to the database.

        This synchronizes the session state with the database without
        committing the transaction. Use this to get generated values
        or ensure constraints are checked.
        """
        self.session.flush()

    def _delete(self, entity: T) -> None:
        """Mark an entity for deletion.

        Args:
            entity: Model instance to delete.
        """
        self.session.delete(entity)


__all__ = ["BaseRepository"]
