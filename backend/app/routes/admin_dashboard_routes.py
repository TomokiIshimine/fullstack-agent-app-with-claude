"""Admin dashboard routes for statistics and analytics."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal, cast

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

from app.constants.http import HTTP_OK
from app.routes.dependencies import with_admin_dashboard_service
from app.services.admin_dashboard_service import AdminDashboardService
from app.utils.auth_decorator import require_auth, require_role

TrendMetric = Literal["conversations", "messages", "tokens"]

logger = logging.getLogger(__name__)

admin_dashboard_bp = Blueprint("admin_dashboard", __name__, url_prefix="/admin/dashboard")


@admin_dashboard_bp.get("/summary")
@require_auth
@require_role("admin")
@with_admin_dashboard_service
def get_summary(*, admin_dashboard_service: AdminDashboardService):
    """
    Get dashboard summary statistics.

    Returns:
        {
            "total_users": 100,
            "active_users": 42,
            "total_conversations": 500,
            "today_conversations": 15,
            "total_messages": 3000,
            "total_tokens": {
                "input": 100000,
                "output": 50000
            },
            "total_cost_usd": 25.50
        }
    """
    logger.info("GET /api/admin/dashboard/summary - Retrieving dashboard summary")

    response = admin_dashboard_service.get_summary()

    logger.info(
        "GET /api/admin/dashboard/summary - Summary retrieved",
        extra={"total_users": response.total_users},
    )
    return jsonify(response.model_dump()), HTTP_OK


@admin_dashboard_bp.get("/trends")
@require_auth
@require_role("admin")
@with_admin_dashboard_service
def get_trends(*, admin_dashboard_service: AdminDashboardService):
    """
    Get trend data for charts.

    Query parameters:
        - period: 7d | 30d | 90d | custom (default: 30d)
        - metric: conversations | messages | tokens (default: conversations)
        - start_date: YYYY-MM-DD (required if period=custom)
        - end_date: YYYY-MM-DD (required if period=custom)

    Returns:
        {
            "period": "30d",
            "metric": "conversations",
            "data": [
                {"date": "2025-01-01", "value": 42},
                {"date": "2025-01-02", "value": 38},
                ...
            ]
        }
    """
    period = request.args.get("period", "30d")
    metric = request.args.get("metric", "conversations")
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    # Validate period
    valid_periods = ["7d", "30d", "90d", "custom"]
    if period not in valid_periods:
        raise BadRequest(f"Invalid period. Must be one of: {', '.join(valid_periods)}")

    # Validate metric
    valid_metrics = ["conversations", "messages", "tokens"]
    if metric not in valid_metrics:
        raise BadRequest(f"Invalid metric. Must be one of: {', '.join(valid_metrics)}")

    # Parse dates for custom period
    start_date = None
    end_date = None
    if period == "custom":
        if not start_date_str or not end_date_str:
            raise BadRequest("start_date and end_date are required for custom period")
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise BadRequest("Invalid date format. Use YYYY-MM-DD")

        if start_date > end_date:
            raise BadRequest("start_date must be before or equal to end_date")

    logger.info(
        "GET /api/admin/dashboard/trends - Retrieving trends",
        extra={"period": period, "metric": metric},
    )

    response = admin_dashboard_service.get_trends(
        period=period,
        metric=cast(TrendMetric, metric),
        start_date=start_date,
        end_date=end_date,
    )

    logger.info(
        "GET /api/admin/dashboard/trends - Trends retrieved",
        extra={"data_points": len(response.data)},
    )
    return jsonify(response.model_dump(mode="json")), HTTP_OK


@admin_dashboard_bp.get("/rankings")
@require_auth
@require_role("admin")
@with_admin_dashboard_service
def get_rankings(*, admin_dashboard_service: AdminDashboardService):
    """
    Get user rankings by metric.

    Query parameters:
        - metric: conversations | messages | tokens (default: conversations)
        - limit: number (default: 10, max: 50)
        - period: 7d | 30d | 90d | all (default: all)

    Returns:
        {
            "metric": "conversations",
            "rankings": [
                {"user_id": 1, "email": "user@example.com", "name": "User", "value": 150},
                ...
            ]
        }
    """
    metric = request.args.get("metric", "conversations")
    limit = request.args.get("limit", 10, type=int)
    period = request.args.get("period", "all")

    # Validate metric
    valid_metrics = ["conversations", "messages", "tokens"]
    if metric not in valid_metrics:
        raise BadRequest(f"Invalid metric. Must be one of: {', '.join(valid_metrics)}")

    # Validate period
    valid_periods = ["7d", "30d", "90d", "all"]
    if period not in valid_periods:
        raise BadRequest(f"Invalid period. Must be one of: {', '.join(valid_periods)}")

    logger.info(
        "GET /api/admin/dashboard/rankings - Retrieving rankings",
        extra={"metric": metric, "limit": limit, "period": period},
    )

    response = admin_dashboard_service.get_rankings(
        metric=cast(TrendMetric, metric),
        limit=limit,
        period=period,
    )

    logger.info(
        "GET /api/admin/dashboard/rankings - Rankings retrieved",
        extra={"count": len(response.rankings)},
    )
    return jsonify(response.model_dump()), HTTP_OK


__all__ = ["admin_dashboard_bp"]
