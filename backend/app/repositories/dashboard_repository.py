"""Dashboard repository for statistics queries."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any, Literal

from sqlalchemy import func

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.repositories.base import BaseRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class DashboardRepository(BaseRepository):
    """Repository for dashboard statistics queries."""

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session."""
        super().__init__(session)

    def count_total_users(self) -> int:
        """Count total number of users."""
        return self.session.query(func.count(User.id)).scalar() or 0

    def count_active_users(self, days: int = 7) -> int:
        """Count users who have had conversations in the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return self.session.query(func.count(func.distinct(Conversation.user_id))).filter(Conversation.created_at >= cutoff).scalar() or 0

    def count_total_conversations(self) -> int:
        """Count total number of conversations."""
        return self.session.query(func.count(Conversation.id)).scalar() or 0

    def count_today_conversations(self) -> int:
        """Count conversations created today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.session.query(func.count(Conversation.id)).filter(Conversation.created_at >= today_start).scalar() or 0

    def count_total_messages(self) -> int:
        """Count total number of messages."""
        return self.session.query(func.count(Message.id)).scalar() or 0

    def sum_tokens(self) -> tuple[int, int]:
        """Sum all input and output tokens.

        Returns:
            Tuple of (total_input_tokens, total_output_tokens)
        """
        result = self.session.query(
            func.coalesce(func.sum(Message.input_tokens), 0),
            func.coalesce(func.sum(Message.output_tokens), 0),
        ).first()
        return (int(result[0]), int(result[1])) if result else (0, 0)

    def sum_cost(self) -> float:
        """Sum all cost_usd values."""
        result = self.session.query(func.coalesce(func.sum(Message.cost_usd), 0)).scalar()
        return float(result) if result else 0.0

    def get_conversation_trends(
        self,
        days: int = 30,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[tuple[date, int]]:
        """Get daily conversation counts for trend chart.

        Args:
            days: Number of days to include (default 30)
            start_date: Optional start date (overrides days)
            end_date: Optional end date (defaults to today)

        Returns:
            List of (date, count) tuples
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=days - 1)

        # Convert to datetime for comparison
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        results = (
            self.session.query(
                func.date(Conversation.created_at).label("date"),
                func.count(Conversation.id).label("count"),
            )
            .filter(Conversation.created_at >= start_dt)
            .filter(Conversation.created_at <= end_dt)
            .group_by(func.date(Conversation.created_at))
            .order_by(func.date(Conversation.created_at))
            .all()
        )

        # Convert to dict for easy lookup
        result_dict = {row.date: row.count for row in results}

        # Fill in missing dates with 0
        all_dates = []
        current = start_date
        while current <= end_date:
            count = result_dict.get(current, 0)
            all_dates.append((current, count))
            current += timedelta(days=1)

        return all_dates

    def get_message_trends(
        self,
        days: int = 30,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[tuple[date, int]]:
        """Get daily message counts for trend chart.

        Args:
            days: Number of days to include (default 30)
            start_date: Optional start date (overrides days)
            end_date: Optional end date (defaults to today)

        Returns:
            List of (date, count) tuples
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=days - 1)

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        results = (
            self.session.query(
                func.date(Message.created_at).label("date"),
                func.count(Message.id).label("count"),
            )
            .filter(Message.created_at >= start_dt)
            .filter(Message.created_at <= end_dt)
            .group_by(func.date(Message.created_at))
            .order_by(func.date(Message.created_at))
            .all()
        )

        result_dict = {row.date: row.count for row in results}

        all_dates = []
        current = start_date
        while current <= end_date:
            count = result_dict.get(current, 0)
            all_dates.append((current, count))
            current += timedelta(days=1)

        return all_dates

    def get_token_trends(
        self,
        days: int = 30,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[tuple[date, int]]:
        """Get daily token consumption for trend chart.

        Args:
            days: Number of days to include (default 30)
            start_date: Optional start date (overrides days)
            end_date: Optional end date (defaults to today)

        Returns:
            List of (date, total_tokens) tuples
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=days - 1)

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        results = (
            self.session.query(
                func.date(Message.created_at).label("date"),
                (func.coalesce(func.sum(Message.input_tokens), 0) + func.coalesce(func.sum(Message.output_tokens), 0)).label("total_tokens"),
            )
            .filter(Message.created_at >= start_dt)
            .filter(Message.created_at <= end_dt)
            .group_by(func.date(Message.created_at))
            .order_by(func.date(Message.created_at))
            .all()
        )

        result_dict = {row.date: int(row.total_tokens) for row in results}

        all_dates = []
        current = start_date
        while current <= end_date:
            count = result_dict.get(current, 0)
            all_dates.append((current, count))
            current += timedelta(days=1)

        return all_dates

    def get_user_rankings(
        self,
        metric: Literal["conversations", "messages", "tokens"],
        limit: int = 10,
        days: int | None = None,
    ) -> list[tuple[int, str, str | None, int]]:
        """Get top users by specified metric.

        Args:
            metric: Metric to rank by
            limit: Number of users to return
            days: Optional period filter (None = all time)

        Returns:
            List of (user_id, email, name, value) tuples
        """
        cutoff = datetime.utcnow() - timedelta(days=days) if days else None

        query: Any
        if metric == "conversations":
            query = self.session.query(
                User.id,
                User.email,
                User.name,
                func.count(Conversation.id).label("value"),
            ).outerjoin(Conversation, User.id == Conversation.user_id)
            if cutoff:
                query = query.filter(Conversation.created_at >= cutoff)
            query = query.group_by(User.id, User.email, User.name)

        elif metric == "messages":
            query = (
                self.session.query(
                    User.id,
                    User.email,
                    User.name,
                    func.count(Message.id).label("value"),
                )
                .outerjoin(Conversation, User.id == Conversation.user_id)
                .outerjoin(Message, Conversation.id == Message.conversation_id)
            )
            if cutoff:
                query = query.filter(Message.created_at >= cutoff)
            query = query.group_by(User.id, User.email, User.name)

        else:  # tokens
            query = (
                self.session.query(
                    User.id,
                    User.email,
                    User.name,
                    (func.coalesce(func.sum(Message.input_tokens), 0) + func.coalesce(func.sum(Message.output_tokens), 0)).label("value"),
                )
                .outerjoin(Conversation, User.id == Conversation.user_id)
                .outerjoin(Message, Conversation.id == Message.conversation_id)
            )
            if cutoff:
                query = query.filter(Message.created_at >= cutoff)
            query = query.group_by(User.id, User.email, User.name)

        results = query.order_by(func.count(User.id).desc()).limit(limit).all()
        return [(row[0], row[1], row[2], int(row[3])) for row in results]


__all__ = ["DashboardRepository"]
