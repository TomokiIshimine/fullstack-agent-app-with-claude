"""Tests for AdminDashboardService (admin dashboard business logic)."""

from __future__ import annotations

from datetime import date
from unittest.mock import Mock

import pytest

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.admin_dashboard import DashboardRankingsResponse, DashboardSummaryResponse, DashboardTrendsResponse
from app.services.admin_dashboard_service import AdminDashboardService


@pytest.fixture
def mock_dashboard_repo():
    """Create a mock DashboardRepository."""
    return Mock(spec=DashboardRepository)


@pytest.fixture
def dashboard_service(app, mock_dashboard_repo):
    """Create AdminDashboardService with mocked repository."""
    from app.database import get_session

    with app.app_context():
        session = get_session()
        service = AdminDashboardService(session)
        # Replace the real repository with mock
        service.dashboard_repo = mock_dashboard_repo
        yield service


class TestGetSummary:
    """Tests for AdminDashboardService.get_summary method."""

    def test_get_summary_returns_response(self, app, dashboard_service, mock_dashboard_repo):
        """Test that get_summary returns DashboardSummaryResponse."""
        mock_dashboard_repo.count_total_users.return_value = 100
        mock_dashboard_repo.count_active_users.return_value = 42
        mock_dashboard_repo.count_total_conversations.return_value = 500
        mock_dashboard_repo.count_today_conversations.return_value = 15
        mock_dashboard_repo.count_total_messages.return_value = 3000
        mock_dashboard_repo.sum_tokens.return_value = (100000, 50000)
        mock_dashboard_repo.sum_cost.return_value = 25.50

        with app.app_context():
            result = dashboard_service.get_summary()

            assert isinstance(result, DashboardSummaryResponse)

    def test_get_summary_calls_all_repos(self, app, dashboard_service, mock_dashboard_repo):
        """Test that get_summary calls all 7 repository methods."""
        mock_dashboard_repo.count_total_users.return_value = 0
        mock_dashboard_repo.count_active_users.return_value = 0
        mock_dashboard_repo.count_total_conversations.return_value = 0
        mock_dashboard_repo.count_today_conversations.return_value = 0
        mock_dashboard_repo.count_total_messages.return_value = 0
        mock_dashboard_repo.sum_tokens.return_value = (0, 0)
        mock_dashboard_repo.sum_cost.return_value = 0.0

        with app.app_context():
            dashboard_service.get_summary()

            mock_dashboard_repo.count_total_users.assert_called_once()
            mock_dashboard_repo.count_active_users.assert_called_once_with(days=7)
            mock_dashboard_repo.count_total_conversations.assert_called_once()
            mock_dashboard_repo.count_today_conversations.assert_called_once()
            mock_dashboard_repo.count_total_messages.assert_called_once()
            mock_dashboard_repo.sum_tokens.assert_called_once()
            mock_dashboard_repo.sum_cost.assert_called_once()

    def test_get_summary_maps_values_correctly(self, app, dashboard_service, mock_dashboard_repo):
        """Test that get_summary maps repository values to response fields."""
        mock_dashboard_repo.count_total_users.return_value = 100
        mock_dashboard_repo.count_active_users.return_value = 42
        mock_dashboard_repo.count_total_conversations.return_value = 500
        mock_dashboard_repo.count_today_conversations.return_value = 15
        mock_dashboard_repo.count_total_messages.return_value = 3000
        mock_dashboard_repo.sum_tokens.return_value = (100000, 50000)
        mock_dashboard_repo.sum_cost.return_value = 25.50

        with app.app_context():
            result = dashboard_service.get_summary()

            assert result.total_users == 100
            assert result.active_users == 42
            assert result.total_conversations == 500
            assert result.today_conversations == 15
            assert result.total_messages == 3000

    def test_get_summary_rounds_cost(self, app, dashboard_service, mock_dashboard_repo):
        """Test that cost is rounded to 2 decimal places."""
        mock_dashboard_repo.count_total_users.return_value = 0
        mock_dashboard_repo.count_active_users.return_value = 0
        mock_dashboard_repo.count_total_conversations.return_value = 0
        mock_dashboard_repo.count_today_conversations.return_value = 0
        mock_dashboard_repo.count_total_messages.return_value = 0
        mock_dashboard_repo.sum_tokens.return_value = (0, 0)
        mock_dashboard_repo.sum_cost.return_value = 25.555555

        with app.app_context():
            result = dashboard_service.get_summary()

            assert result.total_cost_usd == 25.56

    def test_get_summary_token_stats_structure(self, app, dashboard_service, mock_dashboard_repo):
        """Test that total_tokens has input and output fields."""
        mock_dashboard_repo.count_total_users.return_value = 0
        mock_dashboard_repo.count_active_users.return_value = 0
        mock_dashboard_repo.count_total_conversations.return_value = 0
        mock_dashboard_repo.count_today_conversations.return_value = 0
        mock_dashboard_repo.count_total_messages.return_value = 0
        mock_dashboard_repo.sum_tokens.return_value = (100000, 50000)
        mock_dashboard_repo.sum_cost.return_value = 0.0

        with app.app_context():
            result = dashboard_service.get_summary()

            assert result.total_tokens.input == 100000
            assert result.total_tokens.output == 50000


class TestGetTrends:
    """Tests for AdminDashboardService.get_trends method."""

    def test_get_trends_conversations_7d(self, app, dashboard_service, mock_dashboard_repo):
        """Test uses 7 days for '7d' period."""
        mock_dashboard_repo.get_conversation_trends.return_value = []

        with app.app_context():
            dashboard_service.get_trends(period="7d", metric="conversations")

            mock_dashboard_repo.get_conversation_trends.assert_called_once_with(days=7, start_date=None, end_date=None)

    def test_get_trends_conversations_30d(self, app, dashboard_service, mock_dashboard_repo):
        """Test uses 30 days for '30d' period (default)."""
        mock_dashboard_repo.get_conversation_trends.return_value = []

        with app.app_context():
            dashboard_service.get_trends(period="30d", metric="conversations")

            mock_dashboard_repo.get_conversation_trends.assert_called_once_with(days=30, start_date=None, end_date=None)

    def test_get_trends_conversations_90d(self, app, dashboard_service, mock_dashboard_repo):
        """Test uses 90 days for '90d' period."""
        mock_dashboard_repo.get_conversation_trends.return_value = []

        with app.app_context():
            dashboard_service.get_trends(period="90d", metric="conversations")

            mock_dashboard_repo.get_conversation_trends.assert_called_once_with(days=90, start_date=None, end_date=None)

    def test_get_trends_custom_period(self, app, dashboard_service, mock_dashboard_repo):
        """Test uses start_date and end_date for 'custom' period."""
        mock_dashboard_repo.get_conversation_trends.return_value = []
        start = date(2025, 1, 1)
        end = date(2025, 1, 10)

        with app.app_context():
            dashboard_service.get_trends(period="custom", metric="conversations", start_date=start, end_date=end)

            mock_dashboard_repo.get_conversation_trends.assert_called_once_with(days=10, start_date=start, end_date=end)

    def test_get_trends_messages_metric(self, app, dashboard_service, mock_dashboard_repo):
        """Test calls get_message_trends for messages metric."""
        mock_dashboard_repo.get_message_trends.return_value = []

        with app.app_context():
            dashboard_service.get_trends(period="30d", metric="messages")

            mock_dashboard_repo.get_message_trends.assert_called_once()
            mock_dashboard_repo.get_conversation_trends.assert_not_called()
            mock_dashboard_repo.get_token_trends.assert_not_called()

    def test_get_trends_tokens_metric(self, app, dashboard_service, mock_dashboard_repo):
        """Test calls get_token_trends for tokens metric."""
        mock_dashboard_repo.get_token_trends.return_value = []

        with app.app_context():
            dashboard_service.get_trends(period="30d", metric="tokens")

            mock_dashboard_repo.get_token_trends.assert_called_once()
            mock_dashboard_repo.get_conversation_trends.assert_not_called()
            mock_dashboard_repo.get_message_trends.assert_not_called()

    def test_get_trends_returns_response(self, app, dashboard_service, mock_dashboard_repo):
        """Test returns DashboardTrendsResponse."""
        mock_dashboard_repo.get_conversation_trends.return_value = []

        with app.app_context():
            result = dashboard_service.get_trends(period="30d", metric="conversations")

            assert isinstance(result, DashboardTrendsResponse)

    def test_get_trends_data_point_structure(self, app, dashboard_service, mock_dashboard_repo):
        """Test data points have date and value."""
        mock_dashboard_repo.get_conversation_trends.return_value = [
            (date(2025, 1, 1), 10),
            (date(2025, 1, 2), 20),
        ]

        with app.app_context():
            result = dashboard_service.get_trends(period="30d", metric="conversations")

            assert len(result.data) == 2
            assert result.data[0].date == date(2025, 1, 1)
            assert result.data[0].value == 10
            assert result.data[1].date == date(2025, 1, 2)
            assert result.data[1].value == 20

    def test_get_trends_default_period(self, app, dashboard_service, mock_dashboard_repo):
        """Test defaults to 30d when period not in map."""
        mock_dashboard_repo.get_conversation_trends.return_value = []

        with app.app_context():
            dashboard_service.get_trends(period="invalid", metric="conversations")

            mock_dashboard_repo.get_conversation_trends.assert_called_once_with(days=30, start_date=None, end_date=None)

    def test_get_trends_response_includes_period_and_metric(self, app, dashboard_service, mock_dashboard_repo):
        """Test response includes period and metric."""
        mock_dashboard_repo.get_conversation_trends.return_value = []

        with app.app_context():
            result = dashboard_service.get_trends(period="7d", metric="conversations")

            assert result.period == "7d"
            assert result.metric == "conversations"


class TestGetRankings:
    """Tests for AdminDashboardService.get_rankings method."""

    def test_get_rankings_conversations(self, app, dashboard_service, mock_dashboard_repo):
        """Test calls repo with metric='conversations'."""
        mock_dashboard_repo.get_user_rankings.return_value = []

        with app.app_context():
            dashboard_service.get_rankings(metric="conversations")

            mock_dashboard_repo.get_user_rankings.assert_called_once()
            call_args = mock_dashboard_repo.get_user_rankings.call_args
            assert call_args.kwargs["metric"] == "conversations"

    def test_get_rankings_messages(self, app, dashboard_service, mock_dashboard_repo):
        """Test calls repo with metric='messages'."""
        mock_dashboard_repo.get_user_rankings.return_value = []

        with app.app_context():
            dashboard_service.get_rankings(metric="messages")

            call_args = mock_dashboard_repo.get_user_rankings.call_args
            assert call_args.kwargs["metric"] == "messages"

    def test_get_rankings_tokens(self, app, dashboard_service, mock_dashboard_repo):
        """Test calls repo with metric='tokens'."""
        mock_dashboard_repo.get_user_rankings.return_value = []

        with app.app_context():
            dashboard_service.get_rankings(metric="tokens")

            call_args = mock_dashboard_repo.get_user_rankings.call_args
            assert call_args.kwargs["metric"] == "tokens"

    def test_get_rankings_limit_clamping_min(self, app, dashboard_service, mock_dashboard_repo):
        """Test clamps limit to 1 minimum."""
        mock_dashboard_repo.get_user_rankings.return_value = []

        with app.app_context():
            dashboard_service.get_rankings(metric="conversations", limit=0)

            call_args = mock_dashboard_repo.get_user_rankings.call_args
            assert call_args.kwargs["limit"] == 1

    def test_get_rankings_limit_clamping_negative(self, app, dashboard_service, mock_dashboard_repo):
        """Test clamps negative limit to 1."""
        mock_dashboard_repo.get_user_rankings.return_value = []

        with app.app_context():
            dashboard_service.get_rankings(metric="conversations", limit=-5)

            call_args = mock_dashboard_repo.get_user_rankings.call_args
            assert call_args.kwargs["limit"] == 1

    def test_get_rankings_limit_clamping_max(self, app, dashboard_service, mock_dashboard_repo):
        """Test clamps limit to 50 maximum."""
        mock_dashboard_repo.get_user_rankings.return_value = []

        with app.app_context():
            dashboard_service.get_rankings(metric="conversations", limit=100)

            call_args = mock_dashboard_repo.get_user_rankings.call_args
            assert call_args.kwargs["limit"] == 50

    def test_get_rankings_limit_within_range(self, app, dashboard_service, mock_dashboard_repo):
        """Test limit within range is not modified."""
        mock_dashboard_repo.get_user_rankings.return_value = []

        with app.app_context():
            dashboard_service.get_rankings(metric="conversations", limit=25)

            call_args = mock_dashboard_repo.get_user_rankings.call_args
            assert call_args.kwargs["limit"] == 25

    def test_get_rankings_period_7d(self, app, dashboard_service, mock_dashboard_repo):
        """Test converts '7d' to days=7."""
        mock_dashboard_repo.get_user_rankings.return_value = []

        with app.app_context():
            dashboard_service.get_rankings(metric="conversations", period="7d")

            call_args = mock_dashboard_repo.get_user_rankings.call_args
            assert call_args.kwargs["days"] == 7

    def test_get_rankings_period_30d(self, app, dashboard_service, mock_dashboard_repo):
        """Test converts '30d' to days=30."""
        mock_dashboard_repo.get_user_rankings.return_value = []

        with app.app_context():
            dashboard_service.get_rankings(metric="conversations", period="30d")

            call_args = mock_dashboard_repo.get_user_rankings.call_args
            assert call_args.kwargs["days"] == 30

    def test_get_rankings_period_90d(self, app, dashboard_service, mock_dashboard_repo):
        """Test converts '90d' to days=90."""
        mock_dashboard_repo.get_user_rankings.return_value = []

        with app.app_context():
            dashboard_service.get_rankings(metric="conversations", period="90d")

            call_args = mock_dashboard_repo.get_user_rankings.call_args
            assert call_args.kwargs["days"] == 90

    def test_get_rankings_period_all(self, app, dashboard_service, mock_dashboard_repo):
        """Test uses days=None for 'all' period."""
        mock_dashboard_repo.get_user_rankings.return_value = []

        with app.app_context():
            dashboard_service.get_rankings(metric="conversations", period="all")

            call_args = mock_dashboard_repo.get_user_rankings.call_args
            assert call_args.kwargs["days"] is None

    def test_get_rankings_returns_response(self, app, dashboard_service, mock_dashboard_repo):
        """Test returns DashboardRankingsResponse."""
        mock_dashboard_repo.get_user_rankings.return_value = []

        with app.app_context():
            result = dashboard_service.get_rankings(metric="conversations")

            assert isinstance(result, DashboardRankingsResponse)

    def test_get_rankings_user_item_structure(self, app, dashboard_service, mock_dashboard_repo):
        """Test rankings have user_id, email, name, value."""
        mock_dashboard_repo.get_user_rankings.return_value = [
            (1, "user1@example.com", "User One", 100),
            (2, "user2@example.com", None, 50),
        ]

        with app.app_context():
            result = dashboard_service.get_rankings(metric="conversations")

            assert len(result.rankings) == 2
            assert result.rankings[0].user_id == 1
            assert result.rankings[0].email == "user1@example.com"
            assert result.rankings[0].name == "User One"
            assert result.rankings[0].value == 100
            assert result.rankings[1].name is None

    def test_get_rankings_response_includes_metric(self, app, dashboard_service, mock_dashboard_repo):
        """Test response includes metric."""
        mock_dashboard_repo.get_user_rankings.return_value = []

        with app.app_context():
            result = dashboard_service.get_rankings(metric="tokens")

            assert result.metric == "tokens"
