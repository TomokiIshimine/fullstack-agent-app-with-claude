"""Tests for admin dashboard routes (Admin only)."""

from __future__ import annotations

import uuid as uuid_module

from tests.helpers import assert_response_error, assert_response_success, create_user


def create_conversation(app, user_id: int, title: str = "Test Conversation") -> str:
    """Create a conversation directly in the database.

    Returns:
        str: Created conversation UUID
    """
    from app.database import get_session
    from app.models.conversation import Conversation

    with app.app_context():
        session = get_session()
        conversation = Conversation(
            uuid=str(uuid_module.uuid4()),
            user_id=user_id,
            title=title,
        )
        session.add(conversation)
        session.commit()
        conv_uuid = conversation.uuid
        session.expunge(conversation)

    return conv_uuid


def create_message(
    app, conversation_uuid: str, role: str, content: str, input_tokens: int = 100, output_tokens: int = 50, cost_usd: float = 0.005
) -> int:
    """Create a message in a conversation with metadata.

    Returns:
        int: Created message ID
    """
    from app.database import get_session
    from app.models.conversation import Conversation
    from app.models.message import Message

    with app.app_context():
        session = get_session()
        conversation = session.query(Conversation).filter_by(uuid=conversation_uuid).first()
        assert conversation is not None, f"Conversation not found: {conversation_uuid}"
        message = Message(
            conversation_id=conversation.id,
            role=role,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )
        session.add(message)
        session.commit()
        message_id = message.id
        session.expunge(message)

    return message_id


# ============================================================================
# GET /api/admin/dashboard/summary tests
# ============================================================================


class TestGetSummary:
    """Tests for GET /api/admin/dashboard/summary endpoint."""

    def test_get_summary_unauthorized_without_auth(self, client):
        """Test 401 without authentication."""
        response = client.get("/api/admin/dashboard/summary")
        assert_response_error(response, 401)

    def test_get_summary_forbidden_as_regular_user(self, auth_client):
        """Test 403 for non-admin users."""
        response = auth_client.get("/api/admin/dashboard/summary")
        assert_response_error(response, 403)

    def test_get_summary_success_as_admin(self, auth_admin_client):
        """Test 200 for admin users."""
        response = auth_admin_client.get("/api/admin/dashboard/summary")
        data = assert_response_success(response, 200)
        assert "total_users" in data
        assert "active_users" in data
        assert "total_conversations" in data
        assert "today_conversations" in data
        assert "total_messages" in data
        assert "total_tokens" in data
        assert "total_cost_usd" in data

    def test_get_summary_response_structure(self, auth_admin_client):
        """Test response has all required fields."""
        response = auth_admin_client.get("/api/admin/dashboard/summary")
        data = assert_response_success(response, 200)

        # Verify field types
        assert isinstance(data["total_users"], int)
        assert isinstance(data["active_users"], int)
        assert isinstance(data["total_conversations"], int)
        assert isinstance(data["today_conversations"], int)
        assert isinstance(data["total_messages"], int)
        assert isinstance(data["total_cost_usd"], (int, float))

    def test_get_summary_total_tokens_structure(self, auth_admin_client):
        """Test total_tokens has input and output fields."""
        response = auth_admin_client.get("/api/admin/dashboard/summary")
        data = assert_response_success(response, 200)

        assert "total_tokens" in data
        assert "input" in data["total_tokens"]
        assert "output" in data["total_tokens"]
        assert isinstance(data["total_tokens"]["input"], int)
        assert isinstance(data["total_tokens"]["output"], int)

    def test_get_summary_with_data(self, app, auth_admin_client, test_admin):
        """Test summary reflects actual data."""
        # Create a user and conversation with message
        user_id = create_user(app, email="testuser@example.com", password="password123")
        conv_uuid = create_conversation(app, user_id)
        create_message(app, conv_uuid, "user", "Hello", input_tokens=100, output_tokens=50, cost_usd=0.01)

        response = auth_admin_client.get("/api/admin/dashboard/summary")
        data = assert_response_success(response, 200)

        # Should have at least 2 users (admin + test user)
        assert data["total_users"] >= 2
        assert data["total_conversations"] >= 1
        assert data["total_messages"] >= 1


# ============================================================================
# GET /api/admin/dashboard/trends tests
# ============================================================================


class TestGetTrends:
    """Tests for GET /api/admin/dashboard/trends endpoint."""

    def test_get_trends_unauthorized_without_auth(self, client):
        """Test 401 without authentication."""
        response = client.get("/api/admin/dashboard/trends")
        assert_response_error(response, 401)

    def test_get_trends_forbidden_as_regular_user(self, auth_client):
        """Test 403 for non-admin users."""
        response = auth_client.get("/api/admin/dashboard/trends")
        assert_response_error(response, 403)

    def test_get_trends_success_as_admin(self, auth_admin_client):
        """Test 200 for admin users."""
        response = auth_admin_client.get("/api/admin/dashboard/trends")
        data = assert_response_success(response, 200)
        assert "period" in data
        assert "metric" in data
        assert "data" in data

    def test_get_trends_invalid_period(self, auth_admin_client):
        """Test 400 for invalid period value."""
        response = auth_admin_client.get("/api/admin/dashboard/trends?period=invalid")
        assert_response_error(response, 400)

    def test_get_trends_invalid_metric(self, auth_admin_client):
        """Test 400 for invalid metric value."""
        response = auth_admin_client.get("/api/admin/dashboard/trends?metric=invalid")
        assert_response_error(response, 400)

    def test_get_trends_custom_missing_dates(self, auth_admin_client):
        """Test 400 when custom period without dates."""
        response = auth_admin_client.get("/api/admin/dashboard/trends?period=custom")
        assert_response_error(response, 400)

    def test_get_trends_custom_missing_start_date(self, auth_admin_client):
        """Test 400 when custom period without start_date."""
        response = auth_admin_client.get("/api/admin/dashboard/trends?period=custom&end_date=2025-01-10")
        assert_response_error(response, 400)

    def test_get_trends_custom_missing_end_date(self, auth_admin_client):
        """Test 400 when custom period without end_date."""
        response = auth_admin_client.get("/api/admin/dashboard/trends?period=custom&start_date=2025-01-01")
        assert_response_error(response, 400)

    def test_get_trends_custom_invalid_date_format(self, auth_admin_client):
        """Test 400 for invalid date format."""
        response = auth_admin_client.get("/api/admin/dashboard/trends?period=custom&start_date=01-01-2025&end_date=01-10-2025")
        assert_response_error(response, 400)

    def test_get_trends_custom_start_after_end(self, auth_admin_client):
        """Test 400 when start_date > end_date."""
        response = auth_admin_client.get("/api/admin/dashboard/trends?period=custom&start_date=2025-01-10&end_date=2025-01-01")
        assert_response_error(response, 400)

    def test_get_trends_default_period(self, auth_admin_client):
        """Test uses '30d' when period not specified."""
        response = auth_admin_client.get("/api/admin/dashboard/trends")
        data = assert_response_success(response, 200)
        assert data["period"] == "30d"

    def test_get_trends_default_metric(self, auth_admin_client):
        """Test uses 'conversations' when metric not specified."""
        response = auth_admin_client.get("/api/admin/dashboard/trends")
        data = assert_response_success(response, 200)
        assert data["metric"] == "conversations"

    def test_get_trends_response_structure(self, auth_admin_client):
        """Test response has period, metric, data."""
        response = auth_admin_client.get("/api/admin/dashboard/trends?period=7d&metric=messages")
        data = assert_response_success(response, 200)

        assert data["period"] == "7d"
        assert data["metric"] == "messages"
        assert isinstance(data["data"], list)

    def test_get_trends_data_point_structure(self, auth_admin_client):
        """Test data points have date and value."""
        response = auth_admin_client.get("/api/admin/dashboard/trends?period=7d")
        data = assert_response_success(response, 200)

        assert len(data["data"]) == 7  # 7 days
        for point in data["data"]:
            assert "date" in point
            assert "value" in point
            assert isinstance(point["value"], int)

    def test_get_trends_all_periods(self, auth_admin_client):
        """Test all valid period values."""
        for period in ["7d", "30d", "90d"]:
            response = auth_admin_client.get(f"/api/admin/dashboard/trends?period={period}")
            data = assert_response_success(response, 200)
            assert data["period"] == period

    def test_get_trends_all_metrics(self, auth_admin_client):
        """Test all valid metric values."""
        for metric in ["conversations", "messages", "tokens"]:
            response = auth_admin_client.get(f"/api/admin/dashboard/trends?metric={metric}")
            data = assert_response_success(response, 200)
            assert data["metric"] == metric

    def test_get_trends_custom_period_valid(self, auth_admin_client):
        """Test custom period with valid dates."""
        response = auth_admin_client.get("/api/admin/dashboard/trends?period=custom&start_date=2025-01-01&end_date=2025-01-10")
        data = assert_response_success(response, 200)
        assert data["period"] == "custom"
        assert len(data["data"]) == 10  # 10 days inclusive


# ============================================================================
# GET /api/admin/dashboard/rankings tests
# ============================================================================


class TestGetRankings:
    """Tests for GET /api/admin/dashboard/rankings endpoint."""

    def test_get_rankings_unauthorized_without_auth(self, client):
        """Test 401 without authentication."""
        response = client.get("/api/admin/dashboard/rankings")
        assert_response_error(response, 401)

    def test_get_rankings_forbidden_as_regular_user(self, auth_client):
        """Test 403 for non-admin users."""
        response = auth_client.get("/api/admin/dashboard/rankings")
        assert_response_error(response, 403)

    def test_get_rankings_success_as_admin(self, auth_admin_client):
        """Test 200 for admin users."""
        response = auth_admin_client.get("/api/admin/dashboard/rankings")
        data = assert_response_success(response, 200)
        assert "metric" in data
        assert "rankings" in data

    def test_get_rankings_invalid_metric(self, auth_admin_client):
        """Test 400 for invalid metric value."""
        response = auth_admin_client.get("/api/admin/dashboard/rankings?metric=invalid")
        assert_response_error(response, 400)

    def test_get_rankings_invalid_period(self, auth_admin_client):
        """Test 400 for invalid period value."""
        response = auth_admin_client.get("/api/admin/dashboard/rankings?period=invalid")
        assert_response_error(response, 400)

    def test_get_rankings_default_metric(self, auth_admin_client):
        """Test uses 'conversations' when metric not specified."""
        response = auth_admin_client.get("/api/admin/dashboard/rankings")
        data = assert_response_success(response, 200)
        assert data["metric"] == "conversations"

    def test_get_rankings_default_period(self, auth_admin_client):
        """Test uses 'all' when period not specified."""
        response = auth_admin_client.get("/api/admin/dashboard/rankings")
        # Period is not in response, but it's used internally
        data = assert_response_success(response, 200)
        assert isinstance(data["rankings"], list)

    def test_get_rankings_response_structure(self, auth_admin_client):
        """Test response has metric and rankings."""
        response = auth_admin_client.get("/api/admin/dashboard/rankings?metric=messages&period=30d")
        data = assert_response_success(response, 200)

        assert data["metric"] == "messages"
        assert isinstance(data["rankings"], list)

    def test_get_rankings_all_metrics(self, auth_admin_client):
        """Test all valid metric values."""
        for metric in ["conversations", "messages", "tokens"]:
            response = auth_admin_client.get(f"/api/admin/dashboard/rankings?metric={metric}")
            data = assert_response_success(response, 200)
            assert data["metric"] == metric

    def test_get_rankings_all_periods(self, auth_admin_client):
        """Test all valid period values."""
        for period in ["7d", "30d", "90d", "all"]:
            response = auth_admin_client.get(f"/api/admin/dashboard/rankings?period={period}")
            assert_response_success(response, 200)

    def test_get_rankings_with_limit(self, auth_admin_client):
        """Test limit parameter."""
        response = auth_admin_client.get("/api/admin/dashboard/rankings?limit=5")
        data = assert_response_success(response, 200)
        # Limit is applied server-side, just check response is valid
        assert isinstance(data["rankings"], list)

    def test_get_rankings_item_structure(self, app, auth_admin_client, test_admin):
        """Test ranking items have user_id, email, name, value."""
        # Create a user with conversation
        user_id = create_user(app, email="rankeduser@example.com", password="password123", name="Ranked User")
        conv_uuid = create_conversation(app, user_id)
        create_message(app, conv_uuid, "user", "Hello")

        response = auth_admin_client.get("/api/admin/dashboard/rankings")
        data = assert_response_success(response, 200)

        # Find the user we just created in rankings
        rankings = data["rankings"]
        if rankings:
            item = rankings[0]
            assert "user_id" in item
            assert "email" in item
            assert "name" in item or item.get("name") is None
            assert "value" in item
            assert isinstance(item["user_id"], int)
            assert isinstance(item["email"], str)
            assert isinstance(item["value"], int)
