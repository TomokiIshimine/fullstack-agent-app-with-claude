"""Dashboard repository for statistics queries."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any, Literal

from sqlalchemy import ColumnElement, func
from sqlalchemy.orm.attributes import InstrumentedAttribute

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

    def _get_trends_base(
        self,
        date_field: ColumnElement[Any] | InstrumentedAttribute[datetime],
        value_expr: ColumnElement[Any],
        days: int = 30,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[tuple[date, int]]:
        """Base method for trend data retrieval.

        Args:
            date_field: The datetime field to group by (e.g., Conversation.created_at)
            value_expr: The aggregation expression (e.g., func.count(Conversation.id))
            days: Number of days to include (default 30)
            start_date: Optional start date (overrides days)
            end_date: Optional end date (defaults to today)

        Returns:
            List of (date, value) tuples with missing dates filled with 0
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
                func.date(date_field).label("date"),
                value_expr.label("value"),
            )
            .filter(date_field >= start_dt)
            .filter(date_field <= end_dt)
            .group_by(func.date(date_field))
            .order_by(func.date(date_field))
            .all()
        )

        # Note: func.date() returns string on SQLite, date on MySQL - normalize to date
        result_dict: dict[date, int] = {}
        for row in results:
            row_date = row.date if isinstance(row.date, date) else date.fromisoformat(str(row.date))
            result_dict[row_date] = int(row.value)

        # Fill in missing dates with 0
        all_dates: list[tuple[date, int]] = []
        current = start_date
        while current <= end_date:
            value = result_dict.get(current, 0)
            all_dates.append((current, value))
            current += timedelta(days=1)

        return all_dates

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
        return self._get_trends_base(
            date_field=Conversation.created_at,
            value_expr=func.count(Conversation.id),
            days=days,
            start_date=start_date,
            end_date=end_date,
        )

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
        return self._get_trends_base(
            date_field=Message.created_at,
            value_expr=func.count(Message.id),
            days=days,
            start_date=start_date,
            end_date=end_date,
        )

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
        return self._get_trends_base(
            date_field=Message.created_at,
            value_expr=(func.coalesce(func.sum(Message.input_tokens), 0) + func.coalesce(func.sum(Message.output_tokens), 0)),
            days=days,
            start_date=start_date,
            end_date=end_date,
        )

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

        # Define metric configurations
        metric_configs: dict[str, dict[str, Any]] = {
            "conversations": {
                "value_expr": func.count(Conversation.id),
                "needs_message_join": False,
                "cutoff_field": Conversation.created_at,
            },
            "messages": {
                "value_expr": func.count(Message.id),
                "needs_message_join": True,
                "cutoff_field": Message.created_at,
            },
            "tokens": {
                "value_expr": (func.coalesce(func.sum(Message.input_tokens), 0) + func.coalesce(func.sum(Message.output_tokens), 0)),
                "needs_message_join": True,
                "cutoff_field": Message.created_at,
            },
        }

        config = metric_configs[metric]
        value_expr: ColumnElement[Any] = config["value_expr"]

        # Build query
        query = self.session.query(
            User.id,
            User.email,
            User.name,
            value_expr.label("value"),
        ).outerjoin(Conversation, User.id == Conversation.user_id)

        if config["needs_message_join"]:
            query = query.outerjoin(Message, Conversation.id == Message.conversation_id)

        if cutoff:
            query = query.filter(config["cutoff_field"] >= cutoff)

        query = query.group_by(User.id, User.email, User.name)

        results = query.order_by(value_expr.desc()).limit(limit).all()
        return [(row[0], row[1], row[2], int(row[3])) for row in results]


__all__ = ["DashboardRepository"]
