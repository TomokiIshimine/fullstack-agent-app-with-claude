"""Tests for suggestion generation endpoint."""

from unittest.mock import MagicMock, patch

# Valid UUID v4 format that doesn't exist in database
NONEXISTENT_UUID = "00000000-0000-4000-8000-000000000000"


class TestSuggestionRoute:
    """Test POST /api/conversations/<uuid>/suggestions endpoint."""

    def test_unauthenticated(self, client):
        """Unauthenticated users should receive 401."""
        response = client.post(f"/api/conversations/{NONEXISTENT_UUID}/suggestions")
        assert response.status_code == 401

    def test_invalid_uuid_format(self, auth_client):
        """Invalid UUID format should return 400."""
        response = auth_client.post("/api/conversations/invalid-uuid/suggestions")
        assert response.status_code == 400

    def test_conversation_not_found(self, auth_client):
        """Non-existent conversation should return 404."""
        response = auth_client.post(f"/api/conversations/{NONEXISTENT_UUID}/suggestions")
        assert response.status_code == 404

    def test_conversation_access_denied(self, app, auth_client, test_user):
        """Accessing another user's conversation should return 403."""
        from app.database import get_session
        from app.models.conversation import Conversation

        with app.app_context():
            session = get_session()
            # Create conversation owned by a different user
            conversation = Conversation(user_id=test_user + 1000, title="Other User Conv")
            session.add(conversation)
            session.commit()
            conv_uuid = conversation.uuid
            session.expunge_all()

        response = auth_client.post(f"/api/conversations/{conv_uuid}/suggestions")
        assert response.status_code == 403

    def test_success(self, app, auth_client, test_user):
        """Successful suggestion generation should return 200 with suggestions."""
        from app.database import get_session
        from app.models.conversation import Conversation
        from app.models.message import Message

        with app.app_context():
            session = get_session()
            conversation = Conversation(user_id=test_user, title="Test Conv")
            session.add(conversation)
            session.flush()

            session.add(Message(conversation_id=conversation.id, role="user", content="Hello"))
            session.add(Message(conversation_id=conversation.id, role="assistant", content="Hi!"))
            session.commit()
            conv_uuid = conversation.uuid
            session.expunge_all()

        suggestions = ["Tell me more", "How does that work?", "Thanks!"]

        # Mock the Anthropic client at the service level
        with patch("app.services.suggestion_service.anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client

            # Build mock tool_use response
            tool_block = MagicMock()
            tool_block.type = "tool_use"
            tool_block.name = "generate_suggestions"
            tool_block.input = {"suggestions": suggestions}

            mock_response = MagicMock()
            mock_response.content = [tool_block]
            mock_client.messages.create.return_value = mock_response

            response = auth_client.post(f"/api/conversations/{conv_uuid}/suggestions")

        assert response.status_code == 200
        data = response.get_json()
        assert "suggestions" in data
        assert data["suggestions"] == suggestions

    def test_llm_error_returns_empty_suggestions(self, app, auth_client, test_user):
        """LLM errors should return 200 with empty suggestions array."""
        from app.database import get_session
        from app.models.conversation import Conversation
        from app.models.message import Message

        with app.app_context():
            session = get_session()
            conversation = Conversation(user_id=test_user, title="Test Conv")
            session.add(conversation)
            session.flush()

            session.add(Message(conversation_id=conversation.id, role="user", content="Hello"))
            session.add(Message(conversation_id=conversation.id, role="assistant", content="Hi!"))
            session.commit()
            conv_uuid = conversation.uuid
            session.expunge_all()

        with patch("app.services.suggestion_service.anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = Exception("API error")

            response = auth_client.post(f"/api/conversations/{conv_uuid}/suggestions")

        assert response.status_code == 200
        data = response.get_json()
        assert data["suggestions"] == []

    def test_empty_conversation_returns_empty_suggestions(self, app, auth_client, test_user):
        """Conversation with no messages should return empty suggestions."""
        from app.database import get_session
        from app.models.conversation import Conversation

        with app.app_context():
            session = get_session()
            conversation = Conversation(user_id=test_user, title="Empty Conv")
            session.add(conversation)
            session.commit()
            conv_uuid = conversation.uuid
            session.expunge_all()

        response = auth_client.post(f"/api/conversations/{conv_uuid}/suggestions")

        assert response.status_code == 200
        data = response.get_json()
        assert data["suggestions"] == []
