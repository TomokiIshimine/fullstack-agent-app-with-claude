"""Admin dashboard request/response schemas."""

from __future__ import annotations

import datetime

from pydantic import BaseModel


class TokenStats(BaseModel):
    """Token statistics."""

    input: int
    output: int


class DashboardSummaryResponse(BaseModel):
    """Response schema for dashboard summary."""

    total_users: int
    active_users: int
    total_conversations: int
    today_conversations: int
    total_messages: int
    total_tokens: TokenStats
    total_cost_usd: float


class TrendDataPoint(BaseModel):
    """Single data point for trend chart."""

    date: datetime.date
    value: int


class DashboardTrendsResponse(BaseModel):
    """Response schema for dashboard trends."""

    period: str
    metric: str
    data: list[TrendDataPoint]


class UserRankingItem(BaseModel):
    """Single user in ranking."""

    user_id: int
    email: str
    name: str | None
    value: int


class DashboardRankingsResponse(BaseModel):
    """Response schema for dashboard rankings."""

    metric: str
    rankings: list[UserRankingItem]


__all__ = [
    "TokenStats",
    "DashboardSummaryResponse",
    "TrendDataPoint",
    "DashboardTrendsResponse",
    "UserRankingItem",
    "DashboardRankingsResponse",
]
