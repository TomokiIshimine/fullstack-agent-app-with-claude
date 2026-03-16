"""Tests for SuggestionService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import ConversationAccessDeniedError, ConversationNotFoundError
from app.services.suggestion_service import SuggestionService


@pytest.fixture
def mock_client():
    """Create a mock Anthropic client."""
    return MagicMock()


@pytest.fixture
def suggestion_service(app, mock_client):
    """Create SuggestionService instance with test database session and mock client."""
    from app.database import get_session

    with app.app_context():
        session = get_session()
        yield SuggestionService(session, client=mock_client)


@pytest.fixture
def conversation_with_messages(app, test_user):
    """Create a conversation with messages for testing."""
    from app.database import get_session
    from app.models.conversation import Conversation
    from app.models.message import Message

    with app.app_context():
        session = get_session()

        conversation = Conversation(user_id=test_user, title="Test Conversation")
        session.add(conversation)
        session.flush()

        messages = [
            Message(conversation_id=conversation.id, role="user", content="Hello"),
            Message(conversation_id=conversation.id, role="assistant", content="Hi there!"),
            Message(conversation_id=conversation.id, role="user", content="How are you?"),
            Message(conversation_id=conversation.id, role="assistant", content="I'm doing great!"),
        ]
        session.add_all(messages)
        session.commit()

        conv_uuid = conversation.uuid
        session.expunge_all()

    return {"uuid": conv_uuid, "user_id": test_user}


@pytest.fixture
def conversation_many_messages(app, test_user):
    """Create a conversation with more than SUGGESTION_MESSAGE_LIMIT messages."""
    from app.database import get_session
    from app.models.conversation import Conversation
    from app.models.message import Message

    with app.app_context():
        session = get_session()

        conversation = Conversation(user_id=test_user, title="Long Conversation")
        session.add(conversation)
        session.flush()

        messages = []
        for i in range(10):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append(Message(conversation_id=conversation.id, role=role, content=f"Message {i}"))
        session.add_all(messages)
        session.commit()

        conv_uuid = conversation.uuid
        session.expunge_all()

    return {"uuid": conv_uuid, "user_id": test_user}


@pytest.fixture
def conversation_empty(app, test_user):
    """Create a conversation with no messages."""
    from app.database import get_session
    from app.models.conversation import Conversation

    with app.app_context():
        session = get_session()

        conversation = Conversation(user_id=test_user, title="Empty Conversation")
        session.add(conversation)
        session.commit()

        conv_uuid = conversation.uuid
        session.expunge_all()

    return {"uuid": conv_uuid, "user_id": test_user}


def _make_tool_use_response(suggestions: list[str]):
    """Create a mock Claude API response with tool_use block."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "generate_suggestions"
    tool_block.input = {"suggestions": suggestions}

    response = MagicMock()
    response.content = [tool_block]
    return response


class TestSuggestionServiceInit:
    """Tests for SuggestionService initialization."""

    def test_init_with_client(self, app):
        """Test initialization with provided client."""
        from app.database import get_session

        with app.app_context():
            session = get_session()
            mock_client = MagicMock()
            service = SuggestionService(session, client=mock_client)

            assert service._client is mock_client

    def test_client_lazy_creation(self, app):
        """Test that client is created lazily when accessed."""
        from app.database import get_session

        with app.app_context():
            session = get_session()
            service = SuggestionService(session)

            assert service._client is None

            with patch("app.services.suggestion_service.anthropic.Anthropic") as mock_cls:
                mock_instance = MagicMock()
                mock_cls.return_value = mock_instance

                client = service.client
                assert client is mock_instance
                mock_cls.assert_called_once()


class TestGenerateSuggestions:
    """Tests for SuggestionService.generate_suggestions."""

    def test_success(self, app, suggestion_service, mock_client, conversation_with_messages):
        """Test successful suggestion generation."""
        suggestions = ["Question 1?", "Tell me more", "What about X?"]
        mock_client.messages.create.return_value = _make_tool_use_response(suggestions)

        with app.app_context():
            result = suggestion_service.generate_suggestions(
                uuid=conversation_with_messages["uuid"],
                user_id=conversation_with_messages["user_id"],
            )

        assert result.suggestions == suggestions
        mock_client.messages.create.assert_called_once()

        # Verify the API call arguments
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"
        assert call_kwargs["max_tokens"] == 1024
        assert call_kwargs["system"] is not None
        assert len(call_kwargs["messages"]) == 4
        assert call_kwargs["tool_choice"] == {"type": "tool", "name": "generate_suggestions"}

    def test_conversation_not_found(self, app, suggestion_service, test_user):
        """Test with non-existent conversation UUID."""
        with app.app_context():
            with pytest.raises(ConversationNotFoundError):
                suggestion_service.generate_suggestions(
                    uuid="00000000-0000-4000-8000-000000000000",
                    user_id=test_user,
                )

    def test_conversation_access_denied(self, app, suggestion_service, conversation_with_messages):
        """Test with a different user's conversation."""
        other_user_id = 99999
        with app.app_context():
            with pytest.raises(ConversationAccessDeniedError):
                suggestion_service.generate_suggestions(
                    uuid=conversation_with_messages["uuid"],
                    user_id=other_user_id,
                )

    def test_empty_conversation(self, app, suggestion_service, mock_client, conversation_empty):
        """Test with conversation that has no messages."""
        with app.app_context():
            result = suggestion_service.generate_suggestions(
                uuid=conversation_empty["uuid"],
                user_id=conversation_empty["user_id"],
            )

        assert result.suggestions == []
        mock_client.messages.create.assert_not_called()

    def test_message_limit(self, app, suggestion_service, mock_client, conversation_many_messages):
        """Test that only the most recent messages are sent to Claude API."""
        suggestions = ["Next step?"]
        mock_client.messages.create.return_value = _make_tool_use_response(suggestions)

        with app.app_context():
            suggestion_service.generate_suggestions(
                uuid=conversation_many_messages["uuid"],
                user_id=conversation_many_messages["user_id"],
            )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        # Should only send last 6 messages (SUGGESTION_MESSAGE_LIMIT)
        assert len(call_kwargs["messages"]) == 6
        # Verify the last message is "Message 9"
        assert call_kwargs["messages"][-1]["content"] == "Message 9"

    def test_api_error_returns_empty(self, app, suggestion_service, mock_client, conversation_with_messages):
        """Test that API errors return empty suggestions."""
        mock_client.messages.create.side_effect = Exception("API error")

        with app.app_context():
            result = suggestion_service.generate_suggestions(
                uuid=conversation_with_messages["uuid"],
                user_id=conversation_with_messages["user_id"],
            )

        assert result.suggestions == []

    def test_no_tool_use_block(self, app, suggestion_service, mock_client, conversation_with_messages):
        """Test handling response without tool_use block."""
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Here are some suggestions..."

        response = MagicMock()
        response.content = [text_block]
        mock_client.messages.create.return_value = response

        with app.app_context():
            result = suggestion_service.generate_suggestions(
                uuid=conversation_with_messages["uuid"],
                user_id=conversation_with_messages["user_id"],
            )

        assert result.suggestions == []

    def test_messages_format(self, app, suggestion_service, mock_client, conversation_with_messages):
        """Test that messages are formatted correctly for the API."""
        mock_client.messages.create.return_value = _make_tool_use_response(["test"])

        with app.app_context():
            suggestion_service.generate_suggestions(
                uuid=conversation_with_messages["uuid"],
                user_id=conversation_with_messages["user_id"],
            )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        messages = call_kwargs["messages"]

        # Verify message format
        assert messages[0] == {"role": "user", "content": "Hello"}
        assert messages[1] == {"role": "assistant", "content": "Hi there!"}
        assert messages[2] == {"role": "user", "content": "How are you?"}
        assert messages[3] == {"role": "assistant", "content": "I'm doing great!"}
