"""Tests for admin conversation routes (Admin only)."""

from __future__ import annotations

from datetime import datetime

from tests.helpers import assert_response_error, assert_response_success, create_auth_client, create_user

# Valid UUID v4 format that doesn't exist in database
NONEXISTENT_UUID = "00000000-0000-4000-8000-000000000000"


def create_conversation(app, user_id: int, title: str = "Test Conversation") -> str:
    """Create a conversation directly in the database.

    Args:
        app: Flask application instance
        user_id: Owner user ID
        title: Conversation title

    Returns:
        str: Created conversation UUID
    """
    import uuid as uuid_module

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


def create_message(app, conversation_uuid: str, role: str, content: str) -> int:
    """Create a message in a conversation.

    Args:
        app: Flask application instance
        conversation_uuid: Conversation UUID
        role: Message role ('user' or 'assistant')
        content: Message content

    Returns:
        int: Created message ID
    """
    from app.database import get_session
    from app.models.conversation import Conversation
    from app.models.message import Message

    with app.app_context():
        session = get_session()
        conversation = session.query(Conversation).filter_by(uuid=conversation_uuid).first()
        message = Message(
            conversation_id=conversation.id,
            role=role,
            content=content,
        )
        session.add(message)
        session.commit()
        message_id = message.id
        session.expunge(message)

    return message_id


# GET /api/admin/conversations tests


def test_list_all_conversations_success_as_admin(app):
    """Test that admin can list all conversations from all users."""
    # Create admin and regular users with conversations
    admin_id = create_user(app, email="admin@example.com", password="admin123", role="admin")
    user1_id = create_user(app, email="user1@example.com", password="password123", role="user", name="User One")
    user2_id = create_user(app, email="user2@example.com", password="password123", role="user", name="User Two")

    # Create conversations for each user
    create_conversation(app, user1_id, title="User1 Conversation")
    create_conversation(app, user2_id, title="User2 Conversation")

    admin_client = create_auth_client(app, admin_id, email="admin@example.com", role="admin")

    response = admin_client.get("/api/admin/conversations")

    data = assert_response_success(response, 200)
    assert "conversations" in data
    assert "meta" in data
    assert len(data["conversations"]) == 2

    # Check that conversations include user info
    for conv in data["conversations"]:
        assert "uuid" in conv
        assert "title" in conv
        assert "user" in conv
        assert "id" in conv["user"]
        assert "email" in conv["user"]
        assert "message_count" in conv


def test_list_conversations_with_user_filter(app):
    """Test filtering conversations by user ID."""
    admin_id = create_user(app, email="admin@example.com", password="admin123", role="admin")
    user1_id = create_user(app, email="user1@example.com", password="password123", role="user")
    user2_id = create_user(app, email="user2@example.com", password="password123", role="user")

    # Create conversations for each user
    create_conversation(app, user1_id, title="User1 Conv1")
    create_conversation(app, user1_id, title="User1 Conv2")
    create_conversation(app, user2_id, title="User2 Conv1")

    admin_client = create_auth_client(app, admin_id, email="admin@example.com", role="admin")

    # Filter by user1
    response = admin_client.get(f"/api/admin/conversations?user_id={user1_id}")

    data = assert_response_success(response, 200)
    assert len(data["conversations"]) == 2
    for conv in data["conversations"]:
        assert conv["user"]["id"] == user1_id


def test_list_conversations_with_date_filter(app):
    """Test filtering conversations by date range."""
    from app.database import get_session
    from app.models.conversation import Conversation

    admin_id = create_user(app, email="admin@example.com", password="admin123", role="admin")
    user_id = create_user(app, email="user@example.com", password="password123", role="user")

    # Create conversations with different dates
    conv1_uuid = create_conversation(app, user_id, title="Old Conversation")
    conv2_uuid = create_conversation(app, user_id, title="New Conversation")

    # Manually set dates for testing
    with app.app_context():
        session = get_session()
        old_conv = session.query(Conversation).filter_by(uuid=conv1_uuid).first()
        old_conv.created_at = datetime(2025, 1, 1, 12, 0, 0)
        new_conv = session.query(Conversation).filter_by(uuid=conv2_uuid).first()
        new_conv.created_at = datetime(2025, 12, 15, 12, 0, 0)
        session.commit()

    admin_client = create_auth_client(app, admin_id, email="admin@example.com", role="admin")

    # Filter by date range that includes only the new conversation
    response = admin_client.get("/api/admin/conversations?start_date=2025-12-01&end_date=2025-12-31")

    data = assert_response_success(response, 200)
    assert len(data["conversations"]) == 1
    assert data["conversations"][0]["title"] == "New Conversation"


def test_list_conversations_end_date_includes_entire_day(app):
    """Test that end_date filter includes the entire day."""
    from app.database import get_session
    from app.models.conversation import Conversation

    admin_id = create_user(app, email="admin@example.com", password="admin123", role="admin")
    user_id = create_user(app, email="user@example.com", password="password123", role="user")

    conv_uuid = create_conversation(app, user_id, title="Evening Conversation")

    # Set conversation to late in the day
    with app.app_context():
        session = get_session()
        conv = session.query(Conversation).filter_by(uuid=conv_uuid).first()
        conv.created_at = datetime(2025, 12, 15, 18, 30, 0)  # 6:30 PM
        session.commit()

    admin_client = create_auth_client(app, admin_id, email="admin@example.com", role="admin")

    # Filter by end_date of the same day - should include the conversation
    response = admin_client.get("/api/admin/conversations?end_date=2025-12-15")

    data = assert_response_success(response, 200)
    assert len(data["conversations"]) == 1
    assert data["conversations"][0]["title"] == "Evening Conversation"


def test_list_conversations_pagination(app):
    """Test pagination of conversation list."""
    admin_id = create_user(app, email="admin@example.com", password="admin123", role="admin")
    user_id = create_user(app, email="user@example.com", password="password123", role="user")

    # Create 25 conversations
    for i in range(25):
        create_conversation(app, user_id, title=f"Conversation {i}")

    admin_client = create_auth_client(app, admin_id, email="admin@example.com", role="admin")

    # Get first page
    response = admin_client.get("/api/admin/conversations?page=1&per_page=10")

    data = assert_response_success(response, 200)
    assert len(data["conversations"]) == 10
    assert data["meta"]["total"] == 25
    assert data["meta"]["page"] == 1
    assert data["meta"]["per_page"] == 10
    assert data["meta"]["total_pages"] == 3

    # Get second page
    response = admin_client.get("/api/admin/conversations?page=2&per_page=10")

    data = assert_response_success(response, 200)
    assert len(data["conversations"]) == 10
    assert data["meta"]["page"] == 2


def test_list_conversations_forbidden_as_regular_user(app):
    """Test that regular users cannot list all conversations."""
    user_id = create_user(app, email="user@example.com", password="password123", role="user")
    user_client = create_auth_client(app, user_id, email="user@example.com", role="user")

    response = user_client.get("/api/admin/conversations")

    assert_response_error(response, 403)


def test_list_conversations_unauthorized_without_auth(client):
    """Test that unauthenticated requests are rejected."""
    response = client.get("/api/admin/conversations")

    assert_response_error(response, 401)


# GET /api/admin/conversations/<uuid> tests


def test_get_conversation_detail_success(app):
    """Test that admin can view conversation detail with messages."""
    admin_id = create_user(app, email="admin@example.com", password="admin123", role="admin")
    user_id = create_user(app, email="user@example.com", password="password123", role="user", name="Test User")

    conv_uuid = create_conversation(app, user_id, title="Test Conversation")
    create_message(app, conv_uuid, "user", "Hello!")
    create_message(app, conv_uuid, "assistant", "Hi there!")

    admin_client = create_auth_client(app, admin_id, email="admin@example.com", role="admin")

    response = admin_client.get(f"/api/admin/conversations/{conv_uuid}")

    data = assert_response_success(response, 200)
    assert data["uuid"] == conv_uuid
    assert data["title"] == "Test Conversation"
    assert "user" in data
    assert data["user"]["email"] == "user@example.com"
    assert data["user"]["name"] == "Test User"
    assert "messages" in data
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "Hello!"
    assert data["messages"][1]["role"] == "assistant"
    assert data["messages"][1]["content"] == "Hi there!"


def test_get_conversation_detail_not_found(app):
    """Test that non-existent conversation returns 404."""
    admin_id = create_user(app, email="admin@example.com", password="admin123", role="admin")
    admin_client = create_auth_client(app, admin_id, email="admin@example.com", role="admin")

    response = admin_client.get(f"/api/admin/conversations/{NONEXISTENT_UUID}")

    assert_response_error(response, 404)


def test_get_conversation_detail_invalid_uuid_format(app):
    """Test that invalid UUID format returns 400 Bad Request."""
    admin_id = create_user(app, email="admin@example.com", password="admin123", role="admin")
    admin_client = create_auth_client(app, admin_id, email="admin@example.com", role="admin")

    response = admin_client.get("/api/admin/conversations/invalid-uuid")

    assert_response_error(response, 400)


def test_get_conversation_detail_forbidden_as_regular_user(app):
    """Test that regular users cannot view conversation details via admin endpoint."""
    user_id = create_user(app, email="user@example.com", password="password123", role="user")
    conv_uuid = create_conversation(app, user_id, title="My Conversation")

    user_client = create_auth_client(app, user_id, email="user@example.com", role="user")

    response = user_client.get(f"/api/admin/conversations/{conv_uuid}")

    assert_response_error(response, 403)


def test_get_conversation_detail_unauthorized_without_auth(client):
    """Test that unauthenticated requests are rejected."""
    response = client.get("/api/admin/conversations/some-uuid")

    assert_response_error(response, 401)


# Date validation tests


def test_list_conversations_invalid_start_date_format(app):
    """Test that invalid start_date format returns 400."""
    admin_id = create_user(app, email="admin@example.com", password="admin123", role="admin")
    admin_client = create_auth_client(app, admin_id, email="admin@example.com", role="admin")

    response = admin_client.get("/api/admin/conversations?start_date=invalid-date")

    assert_response_error(response, 400)
    data = response.get_json()
    assert "開始日" in data["error"]


def test_list_conversations_invalid_end_date_format(app):
    """Test that invalid end_date format returns 400."""
    admin_id = create_user(app, email="admin@example.com", password="admin123", role="admin")
    admin_client = create_auth_client(app, admin_id, email="admin@example.com", role="admin")

    response = admin_client.get("/api/admin/conversations?end_date=not-a-date")

    assert_response_error(response, 400)
    data = response.get_json()
    assert "終了日" in data["error"]


def test_list_conversations_valid_date_formats(app):
    """Test that various valid date formats are accepted."""
    admin_id = create_user(app, email="admin@example.com", password="admin123", role="admin")
    admin_client = create_auth_client(app, admin_id, email="admin@example.com", role="admin")

    # ISO date format
    response = admin_client.get("/api/admin/conversations?start_date=2025-01-01&end_date=2025-12-31")
    assert_response_success(response, 200)

    # ISO datetime format with timezone
    response = admin_client.get("/api/admin/conversations?start_date=2025-01-01T00:00:00Z")
    assert_response_success(response, 200)
