"""Tests for DashboardRepository (dashboard statistics data access layer)."""

from __future__ import annotations

import uuid as uuid_module
from datetime import date, datetime, timedelta, timezone

import pytest

from app.repositories.dashboard_repository import DashboardRepository


@pytest.fixture
def dashboard_repo(app):
    """Create DashboardRepository instance with test database session."""
    from app.database import get_session

    with app.app_context():
        session = get_session()
        yield DashboardRepository(session), session


def create_user_direct(app, email: str, role: str = "user", name: str | None = None) -> int:
    """Create a user directly in the database without password for testing."""
    from app.database import get_session
    from app.models.user import User

    with app.app_context():
        session = get_session()
        user = User(email=email, password_hash="dummy_hash", role=role, name=name)
        session.add(user)
        session.commit()
        user_id = user.id
        session.expunge(user)

    return user_id


def create_conversation_on_date(app, user_id: int, target_date: datetime, title: str = "Test Conversation") -> tuple[int, str]:
    """Create a conversation with a specific created_at date.

    Returns:
        Tuple of (conversation_id, conversation_uuid)
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
        session.flush()
        # Manually set created_at
        conversation.created_at = target_date
        session.commit()
        conv_id = conversation.id
        conv_uuid = conversation.uuid
        session.expunge(conversation)

    return conv_id, conv_uuid


def create_message_with_metadata(
    app,
    conversation_id: int,
    role: str = "assistant",
    content: str = "Test message",
    input_tokens: int | None = 100,
    output_tokens: int | None = 50,
    cost_usd: float | None = 0.005,
    created_at: datetime | None = None,
) -> int:
    """Create a message with token and cost metadata."""
    from app.database import get_session
    from app.models.message import Message

    with app.app_context():
        session = get_session()
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )
        session.add(message)
        session.flush()
        if created_at:
            message.created_at = created_at
        session.commit()
        message_id = message.id
        session.expunge(message)

    return message_id


class TestCountTotalUsers:
    """Tests for DashboardRepository.count_total_users method."""

    def test_count_total_users_empty(self, app, dashboard_repo):
        """Test returns 0 when no users exist."""
        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_total_users()
            assert result == 0

    def test_count_total_users_single(self, app, dashboard_repo):
        """Test returns 1 with one user."""
        create_user_direct(app, email="user1@example.com")
        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_total_users()
            assert result == 1

    def test_count_total_users_multiple(self, app, dashboard_repo):
        """Test returns correct count with multiple users."""
        create_user_direct(app, email="user1@example.com")
        create_user_direct(app, email="user2@example.com")
        create_user_direct(app, email="user3@example.com")
        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_total_users()
            assert result == 3

    def test_count_total_users_includes_all_roles(self, app, dashboard_repo):
        """Test counts both admin and regular users."""
        create_user_direct(app, email="admin@example.com", role="admin")
        create_user_direct(app, email="user@example.com", role="user")
        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_total_users()
            assert result == 2


class TestCountActiveUsers:
    """Tests for DashboardRepository.count_active_users method."""

    def test_count_active_users_no_conversations(self, app, dashboard_repo):
        """Test returns 0 when no conversations exist."""
        create_user_direct(app, email="user@example.com")
        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_active_users(days=7)
            assert result == 0

    def test_count_active_users_within_period(self, app, dashboard_repo):
        """Test counts users with recent conversations."""
        user_id = create_user_direct(app, email="user@example.com")
        now = datetime.now(timezone.utc)
        create_conversation_on_date(app, user_id, now - timedelta(days=3))

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_active_users(days=7)
            assert result == 1

    def test_count_active_users_outside_period(self, app, dashboard_repo):
        """Test excludes users with old conversations."""
        user_id = create_user_direct(app, email="user@example.com")
        now = datetime.now(timezone.utc)
        create_conversation_on_date(app, user_id, now - timedelta(days=10))

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_active_users(days=7)
            assert result == 0

    def test_count_active_users_distinct(self, app, dashboard_repo):
        """Test counts each user once even with multiple conversations."""
        user_id = create_user_direct(app, email="user@example.com")
        now = datetime.now(timezone.utc)
        create_conversation_on_date(app, user_id, now - timedelta(days=1))
        create_conversation_on_date(app, user_id, now - timedelta(days=2))
        create_conversation_on_date(app, user_id, now - timedelta(days=3))

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_active_users(days=7)
            assert result == 1

    def test_count_active_users_custom_days(self, app, dashboard_repo):
        """Test respects custom days parameter."""
        user_id = create_user_direct(app, email="user@example.com")
        now = datetime.now(timezone.utc)
        create_conversation_on_date(app, user_id, now - timedelta(days=5))

        repo, session = dashboard_repo
        with app.app_context():
            result_3d = repo.count_active_users(days=3)
            result_7d = repo.count_active_users(days=7)
            assert result_3d == 0
            assert result_7d == 1


class TestCountTotalConversations:
    """Tests for DashboardRepository.count_total_conversations method."""

    def test_count_total_conversations_empty(self, app, dashboard_repo):
        """Test returns 0 when no conversations exist."""
        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_total_conversations()
            assert result == 0

    def test_count_total_conversations_multiple(self, app, dashboard_repo):
        """Test returns correct count with multiple conversations."""
        user_id = create_user_direct(app, email="user@example.com")
        now = datetime.now(timezone.utc)
        create_conversation_on_date(app, user_id, now)
        create_conversation_on_date(app, user_id, now)
        create_conversation_on_date(app, user_id, now)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_total_conversations()
            assert result == 3

    def test_count_total_conversations_multiple_users(self, app, dashboard_repo):
        """Test counts conversations across all users."""
        user1_id = create_user_direct(app, email="user1@example.com")
        user2_id = create_user_direct(app, email="user2@example.com")
        now = datetime.now(timezone.utc)
        create_conversation_on_date(app, user1_id, now)
        create_conversation_on_date(app, user1_id, now)
        create_conversation_on_date(app, user2_id, now)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_total_conversations()
            assert result == 3


class TestCountTodayConversations:
    """Tests for DashboardRepository.count_today_conversations method."""

    def test_count_today_conversations_none(self, app, dashboard_repo):
        """Test returns 0 when no today's conversations."""
        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_today_conversations()
            assert result == 0

    def test_count_today_conversations_today(self, app, dashboard_repo):
        """Test counts conversations created today."""
        user_id = create_user_direct(app, email="user@example.com")
        now = datetime.now(timezone.utc)
        create_conversation_on_date(app, user_id, now)
        create_conversation_on_date(app, user_id, now)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_today_conversations()
            assert result == 2

    def test_count_today_conversations_excludes_yesterday(self, app, dashboard_repo):
        """Test excludes older conversations."""
        user_id = create_user_direct(app, email="user@example.com")
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        create_conversation_on_date(app, user_id, now)
        create_conversation_on_date(app, user_id, yesterday)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_today_conversations()
            assert result == 1


class TestCountTotalMessages:
    """Tests for DashboardRepository.count_total_messages method."""

    def test_count_total_messages_empty(self, app, dashboard_repo):
        """Test returns 0 when no messages exist."""
        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_total_messages()
            assert result == 0

    def test_count_total_messages_multiple(self, app, dashboard_repo):
        """Test returns correct count with multiple messages."""
        user_id = create_user_direct(app, email="user@example.com")
        conv_id, _ = create_conversation_on_date(app, user_id, datetime.now(timezone.utc))
        create_message_with_metadata(app, conv_id, role="user", content="Hello")
        create_message_with_metadata(app, conv_id, role="assistant", content="Hi")
        create_message_with_metadata(app, conv_id, role="user", content="How are you?")

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.count_total_messages()
            assert result == 3


class TestSumTokens:
    """Tests for DashboardRepository.sum_tokens method."""

    def test_sum_tokens_empty(self, app, dashboard_repo):
        """Test returns (0, 0) when no messages exist."""
        repo, session = dashboard_repo
        with app.app_context():
            result = repo.sum_tokens()
            assert result == (0, 0)

    def test_sum_tokens_single_message(self, app, dashboard_repo):
        """Test returns correct tokens for single message."""
        user_id = create_user_direct(app, email="user@example.com")
        conv_id, _ = create_conversation_on_date(app, user_id, datetime.now(timezone.utc))
        create_message_with_metadata(app, conv_id, input_tokens=100, output_tokens=50)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.sum_tokens()
            assert result == (100, 50)

    def test_sum_tokens_multiple_messages(self, app, dashboard_repo):
        """Test sums tokens across all messages."""
        user_id = create_user_direct(app, email="user@example.com")
        conv_id, _ = create_conversation_on_date(app, user_id, datetime.now(timezone.utc))
        create_message_with_metadata(app, conv_id, input_tokens=100, output_tokens=50)
        create_message_with_metadata(app, conv_id, input_tokens=200, output_tokens=100)
        create_message_with_metadata(app, conv_id, input_tokens=300, output_tokens=150)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.sum_tokens()
            assert result == (600, 300)

    def test_sum_tokens_null_values(self, app, dashboard_repo):
        """Test handles null token values (coalesce to 0)."""
        user_id = create_user_direct(app, email="user@example.com")
        conv_id, _ = create_conversation_on_date(app, user_id, datetime.now(timezone.utc))
        create_message_with_metadata(app, conv_id, input_tokens=None, output_tokens=None)
        create_message_with_metadata(app, conv_id, input_tokens=100, output_tokens=50)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.sum_tokens()
            assert result == (100, 50)


class TestSumCost:
    """Tests for DashboardRepository.sum_cost method."""

    def test_sum_cost_empty(self, app, dashboard_repo):
        """Test returns 0.0 when no messages exist."""
        repo, session = dashboard_repo
        with app.app_context():
            result = repo.sum_cost()
            assert result == 0.0

    def test_sum_cost_single_message(self, app, dashboard_repo):
        """Test returns correct cost for single message."""
        user_id = create_user_direct(app, email="user@example.com")
        conv_id, _ = create_conversation_on_date(app, user_id, datetime.now(timezone.utc))
        create_message_with_metadata(app, conv_id, cost_usd=0.005)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.sum_cost()
            assert result == pytest.approx(0.005, rel=1e-6)

    def test_sum_cost_multiple_messages(self, app, dashboard_repo):
        """Test sums cost across all messages."""
        user_id = create_user_direct(app, email="user@example.com")
        conv_id, _ = create_conversation_on_date(app, user_id, datetime.now(timezone.utc))
        create_message_with_metadata(app, conv_id, cost_usd=0.005)
        create_message_with_metadata(app, conv_id, cost_usd=0.010)
        create_message_with_metadata(app, conv_id, cost_usd=0.015)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.sum_cost()
            assert result == pytest.approx(0.030, rel=1e-6)

    def test_sum_cost_null_values(self, app, dashboard_repo):
        """Test handles null cost values."""
        user_id = create_user_direct(app, email="user@example.com")
        conv_id, _ = create_conversation_on_date(app, user_id, datetime.now(timezone.utc))
        create_message_with_metadata(app, conv_id, cost_usd=None)
        create_message_with_metadata(app, conv_id, cost_usd=0.005)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.sum_cost()
            assert result == pytest.approx(0.005, rel=1e-6)


class TestGetConversationTrends:
    """Tests for DashboardRepository.get_conversation_trends method."""

    def test_get_conversation_trends_empty(self, app, dashboard_repo):
        """Test returns zeros for date range with no data."""
        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_conversation_trends(days=7)
            assert len(result) == 7
            assert all(value == 0 for _, value in result)

    def test_get_conversation_trends_with_data(self, app, dashboard_repo):
        """Test returns correct daily counts."""
        user_id = create_user_direct(app, email="user@example.com")
        today = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
        create_conversation_on_date(app, user_id, today)
        create_conversation_on_date(app, user_id, today)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_conversation_trends(days=7)
            assert len(result) == 7
            # Today should have 2 conversations
            today_date = date.today()
            today_value = next((v for d, v in result if d == today_date), 0)
            assert today_value == 2

    def test_get_conversation_trends_fills_missing_dates(self, app, dashboard_repo):
        """Test fills gaps with 0."""
        user_id = create_user_direct(app, email="user@example.com")
        today = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
        # Create conversation only on today, skip other days
        create_conversation_on_date(app, user_id, today)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_conversation_trends(days=7)
            assert len(result) == 7
            # All days except today should be 0
            non_zero_count = sum(1 for _, v in result if v > 0)
            assert non_zero_count == 1

    def test_get_conversation_trends_custom_date_range(self, app, dashboard_repo):
        """Test respects start_date and end_date."""
        user_id = create_user_direct(app, email="user@example.com")
        today = date.today()
        start = today - timedelta(days=3)
        end = today

        # Create conversation within range
        create_conversation_on_date(app, user_id, datetime.combine(today, datetime.min.time().replace(hour=12)))

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_conversation_trends(start_date=start, end_date=end)
            assert len(result) == 4  # 4 days inclusive
            assert result[0][0] == start
            assert result[-1][0] == end


class TestGetMessageTrends:
    """Tests for DashboardRepository.get_message_trends method."""

    def test_get_message_trends_empty(self, app, dashboard_repo):
        """Test returns zeros for empty date range."""
        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_message_trends(days=7)
            assert len(result) == 7
            assert all(value == 0 for _, value in result)

    def test_get_message_trends_with_data(self, app, dashboard_repo):
        """Test returns correct daily message counts."""
        user_id = create_user_direct(app, email="user@example.com")
        today = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
        conv_id, _ = create_conversation_on_date(app, user_id, today)
        create_message_with_metadata(app, conv_id, created_at=today)
        create_message_with_metadata(app, conv_id, created_at=today)
        create_message_with_metadata(app, conv_id, created_at=today)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_message_trends(days=7)
            assert len(result) == 7
            today_date = date.today()
            today_value = next((v for d, v in result if d == today_date), 0)
            assert today_value == 3


class TestGetTokenTrends:
    """Tests for DashboardRepository.get_token_trends method."""

    def test_get_token_trends_empty(self, app, dashboard_repo):
        """Test returns zeros for empty date range."""
        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_token_trends(days=7)
            assert len(result) == 7
            assert all(value == 0 for _, value in result)

    def test_get_token_trends_with_data(self, app, dashboard_repo):
        """Test returns sum of input+output tokens per day."""
        user_id = create_user_direct(app, email="user@example.com")
        today = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
        conv_id, _ = create_conversation_on_date(app, user_id, today)
        # Message with 100 input + 50 output = 150 total
        create_message_with_metadata(app, conv_id, input_tokens=100, output_tokens=50, created_at=today)
        # Message with 200 input + 100 output = 300 total
        create_message_with_metadata(app, conv_id, input_tokens=200, output_tokens=100, created_at=today)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_token_trends(days=7)
            assert len(result) == 7
            today_date = date.today()
            today_value = next((v for d, v in result if d == today_date), 0)
            assert today_value == 450  # 150 + 300

    def test_get_token_trends_null_handling(self, app, dashboard_repo):
        """Test handles null tokens correctly."""
        user_id = create_user_direct(app, email="user@example.com")
        today = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
        conv_id, _ = create_conversation_on_date(app, user_id, today)
        create_message_with_metadata(app, conv_id, input_tokens=None, output_tokens=None, created_at=today)
        create_message_with_metadata(app, conv_id, input_tokens=100, output_tokens=50, created_at=today)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_token_trends(days=7)
            today_date = date.today()
            today_value = next((v for d, v in result if d == today_date), 0)
            assert today_value == 150


class TestGetUserRankings:
    """Tests for DashboardRepository.get_user_rankings method."""

    def test_get_user_rankings_conversations_empty(self, app, dashboard_repo):
        """Test returns empty list when no data."""
        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_user_rankings(metric="conversations", limit=10)
            assert result == []

    def test_get_user_rankings_conversations_ordered(self, app, dashboard_repo):
        """Test returns users ordered by conversation count descending."""
        user1_id = create_user_direct(app, email="user1@example.com", name="User One")
        user2_id = create_user_direct(app, email="user2@example.com", name="User Two")
        now = datetime.now(timezone.utc)
        # User1 has 3 conversations
        create_conversation_on_date(app, user1_id, now)
        create_conversation_on_date(app, user1_id, now)
        create_conversation_on_date(app, user1_id, now)
        # User2 has 1 conversation
        create_conversation_on_date(app, user2_id, now)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_user_rankings(metric="conversations", limit=10)
            assert len(result) == 2
            assert result[0][0] == user1_id  # user_id
            assert result[0][3] == 3  # value (conversation count)
            assert result[1][0] == user2_id
            assert result[1][3] == 1

    def test_get_user_rankings_messages_ordered(self, app, dashboard_repo):
        """Test returns users ordered by message count."""
        user1_id = create_user_direct(app, email="user1@example.com", name="User One")
        user2_id = create_user_direct(app, email="user2@example.com", name="User Two")
        now = datetime.now(timezone.utc)
        conv1_id, _ = create_conversation_on_date(app, user1_id, now)
        conv2_id, _ = create_conversation_on_date(app, user2_id, now)
        # User1 has 5 messages
        for _ in range(5):
            create_message_with_metadata(app, conv1_id, created_at=now)
        # User2 has 2 messages
        for _ in range(2):
            create_message_with_metadata(app, conv2_id, created_at=now)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_user_rankings(metric="messages", limit=10)
            assert len(result) == 2
            assert result[0][0] == user1_id
            assert result[0][3] == 5
            assert result[1][0] == user2_id
            assert result[1][3] == 2

    def test_get_user_rankings_tokens_ordered(self, app, dashboard_repo):
        """Test returns users ordered by token count."""
        user1_id = create_user_direct(app, email="user1@example.com", name="User One")
        user2_id = create_user_direct(app, email="user2@example.com", name="User Two")
        now = datetime.now(timezone.utc)
        conv1_id, _ = create_conversation_on_date(app, user1_id, now)
        conv2_id, _ = create_conversation_on_date(app, user2_id, now)
        # User1 has 300 tokens (100 + 50) * 2
        create_message_with_metadata(app, conv1_id, input_tokens=100, output_tokens=50, created_at=now)
        create_message_with_metadata(app, conv1_id, input_tokens=100, output_tokens=50, created_at=now)
        # User2 has 150 tokens
        create_message_with_metadata(app, conv2_id, input_tokens=100, output_tokens=50, created_at=now)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_user_rankings(metric="tokens", limit=10)
            assert len(result) == 2
            assert result[0][0] == user1_id
            assert result[0][3] == 300
            assert result[1][0] == user2_id
            assert result[1][3] == 150

    def test_get_user_rankings_respects_limit(self, app, dashboard_repo):
        """Test limits result count."""
        now = datetime.now(timezone.utc)
        for i in range(5):
            user_id = create_user_direct(app, email=f"user{i}@example.com")
            create_conversation_on_date(app, user_id, now)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_user_rankings(metric="conversations", limit=3)
            assert len(result) == 3

    def test_get_user_rankings_respects_days_filter(self, app, dashboard_repo):
        """Test filters by time period."""
        user1_id = create_user_direct(app, email="user1@example.com", name="User One")
        user2_id = create_user_direct(app, email="user2@example.com", name="User Two")
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=10)
        # User1 has recent conversation
        create_conversation_on_date(app, user1_id, now)
        # User2 has old conversation
        create_conversation_on_date(app, user2_id, old)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_user_rankings(metric="conversations", limit=10, days=7)
            assert len(result) == 1
            assert result[0][0] == user1_id

    def test_get_user_rankings_all_time(self, app, dashboard_repo):
        """Test returns all-time rankings when days=None."""
        user1_id = create_user_direct(app, email="user1@example.com", name="User One")
        user2_id = create_user_direct(app, email="user2@example.com", name="User Two")
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=100)
        create_conversation_on_date(app, user1_id, now)
        create_conversation_on_date(app, user2_id, old)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_user_rankings(metric="conversations", limit=10, days=None)
            assert len(result) == 2

    def test_get_user_rankings_includes_user_info(self, app, dashboard_repo):
        """Test returns user_id, email, name, value."""
        user_id = create_user_direct(app, email="user@example.com", name="Test User")
        conv_id, _ = create_conversation_on_date(app, user_id, datetime.now(timezone.utc))
        create_message_with_metadata(app, conv_id, input_tokens=100, output_tokens=50)

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_user_rankings(metric="tokens", limit=10)
            assert len(result) == 1
            user_id_result, email, name, value = result[0]
            assert user_id_result == user_id
            assert email == "user@example.com"
            assert name == "Test User"
            assert value == 150

    def test_get_user_rankings_null_name(self, app, dashboard_repo):
        """Test handles users with null names."""
        user_id = create_user_direct(app, email="user@example.com", name=None)
        create_conversation_on_date(app, user_id, datetime.now(timezone.utc))

        repo, session = dashboard_repo
        with app.app_context():
            result = repo.get_user_rankings(metric="conversations", limit=10)
            assert len(result) == 1
            _, _, name, _ = result[0]
            assert name is None
