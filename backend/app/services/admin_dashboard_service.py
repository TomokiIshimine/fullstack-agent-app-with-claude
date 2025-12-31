"""Admin dashboard service for statistics and analytics."""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING, Literal

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.admin_dashboard import (
    DashboardRankingsResponse,
    DashboardSummaryResponse,
    DashboardTrendsResponse,
    TokenStats,
    TrendDataPoint,
    UserRankingItem,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AdminDashboardService:
    """Service for admin dashboard operations."""

    def __init__(self, session: Session):
        """Initialize service with database session.

        Args:
            session: SQLAlchemy database session.
        """
        self.session = session
        self.dashboard_repo = DashboardRepository(session)

    def get_summary(self) -> DashboardSummaryResponse:
        """Get dashboard summary statistics.

        Returns:
            DashboardSummaryResponse with all summary metrics.
        """
        total_users = self.dashboard_repo.count_total_users()
        active_users = self.dashboard_repo.count_active_users(days=7)
        total_conversations = self.dashboard_repo.count_total_conversations()
        today_conversations = self.dashboard_repo.count_today_conversations()
        total_messages = self.dashboard_repo.count_total_messages()
        input_tokens, output_tokens = self.dashboard_repo.sum_tokens()
        total_cost = self.dashboard_repo.sum_cost()

        logger.info(
            "Dashboard summary retrieved",
            extra={
                "total_users": total_users,
                "active_users": active_users,
                "total_conversations": total_conversations,
            },
        )

        return DashboardSummaryResponse(
            total_users=total_users,
            active_users=active_users,
            total_conversations=total_conversations,
            today_conversations=today_conversations,
            total_messages=total_messages,
            total_tokens=TokenStats(input=input_tokens, output=output_tokens),
            total_cost_usd=round(total_cost, 2),
        )

    def get_trends(
        self,
        period: str = "30d",
        metric: Literal["conversations", "messages", "tokens"] = "conversations",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> DashboardTrendsResponse:
        """Get trend data for specified metric and period.

        Args:
            period: Period string (7d, 30d, 90d, or custom)
            metric: Metric to retrieve
            start_date: Optional start date for custom period
            end_date: Optional end date for custom period

        Returns:
            DashboardTrendsResponse with trend data.
        """
        # Parse period to days
        if period == "custom" and start_date and end_date:
            days = (end_date - start_date).days + 1
        else:
            period_map = {"7d": 7, "30d": 30, "90d": 90}
            days = period_map.get(period, 30)
            start_date = None
            end_date = None

        # Get trend data based on metric
        if metric == "conversations":
            raw_data = self.dashboard_repo.get_conversation_trends(days=days, start_date=start_date, end_date=end_date)
        elif metric == "messages":
            raw_data = self.dashboard_repo.get_message_trends(days=days, start_date=start_date, end_date=end_date)
        else:  # tokens
            raw_data = self.dashboard_repo.get_token_trends(days=days, start_date=start_date, end_date=end_date)

        data_points = [TrendDataPoint(date=d, value=v) for d, v in raw_data]

        logger.info(
            "Dashboard trends retrieved",
            extra={"period": period, "metric": metric, "data_points": len(data_points)},
        )

        return DashboardTrendsResponse(
            period=period,
            metric=metric,
            data=data_points,
        )

    def get_rankings(
        self,
        metric: Literal["conversations", "messages", "tokens"] = "conversations",
        limit: int = 10,
        period: str = "all",
    ) -> DashboardRankingsResponse:
        """Get user rankings by specified metric.

        Args:
            metric: Metric to rank by
            limit: Number of users to return (max 50)
            period: Period filter (7d, 30d, 90d, all)

        Returns:
            DashboardRankingsResponse with ranked users.
        """
        # Clamp limit
        limit = max(1, min(limit, 50))

        # Parse period to days
        period_map = {"7d": 7, "30d": 30, "90d": 90}
        days = period_map.get(period)  # None for "all"

        raw_data = self.dashboard_repo.get_user_rankings(metric=metric, limit=limit, days=days)

        rankings = [UserRankingItem(user_id=uid, email=email, name=name, value=value) for uid, email, name, value in raw_data]

        logger.info(
            "Dashboard rankings retrieved",
            extra={"metric": metric, "limit": limit, "period": period},
        )

        return DashboardRankingsResponse(
            metric=metric,
            rankings=rankings,
        )


__all__ = ["AdminDashboardService"]
