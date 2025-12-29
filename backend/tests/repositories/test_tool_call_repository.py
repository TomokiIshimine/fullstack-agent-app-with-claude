"""Tests for ToolCallRepository."""

from __future__ import annotations

import pytest

from app.models.tool_call import ToolCall
from app.repositories.tool_call_repository import ToolCallRepository


@pytest.fixture
def tool_call_repo(app):
    """Create ToolCallRepository instance with test database session."""
    from app.database import get_session

    with app.app_context():
        session = get_session()
        yield ToolCallRepository(session)


@pytest.fixture
def sample_message(app, test_user):
    """Create a sample conversation and message for testing."""
    from app.database import get_session
    from app.models.conversation import Conversation
    from app.models.message import Message

    with app.app_context():
        session = get_session()

        # Create conversation
        conversation = Conversation(
            user_id=test_user,
            title="Test Conversation",
        )
        session.add(conversation)
        session.flush()

        # Create message
        message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content="Test message",
        )
        session.add(message)
        session.commit()

        message_id = message.id
        session.expunge(message)

    return message_id


class TestToolCallRepositoryCreate:
    """Tests for ToolCallRepository.create method."""

    def test_create_tool_call_returns_instance(self, app, tool_call_repo, sample_message):
        """Test that create returns a ToolCall instance."""
        with app.app_context():
            result = tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_123",
                tool_name="add",
                input_data={"a": 1, "b": 2},
            )

            assert isinstance(result, ToolCall)
            assert result.id is not None

    def test_create_tool_call_sets_message_id(self, app, tool_call_repo, sample_message):
        """Test that create sets the message_id correctly."""
        with app.app_context():
            result = tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_123",
                tool_name="add",
                input_data={"a": 1, "b": 2},
            )

            assert result.message_id == sample_message

    def test_create_tool_call_sets_tool_call_id(self, app, tool_call_repo, sample_message):
        """Test that create sets the tool_call_id correctly."""
        with app.app_context():
            result = tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="unique_id_456",
                tool_name="multiply",
                input_data={"a": 3, "b": 4},
            )

            assert result.tool_call_id == "unique_id_456"

    def test_create_tool_call_sets_tool_name(self, app, tool_call_repo, sample_message):
        """Test that create sets the tool_name correctly."""
        with app.app_context():
            result = tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_123",
                tool_name="divide",
                input_data={"a": 10, "b": 2},
            )

            assert result.tool_name == "divide"

    def test_create_tool_call_sets_input_data(self, app, tool_call_repo, sample_message):
        """Test that create sets the input data correctly."""
        input_data = {"a": 100, "b": 50}
        with app.app_context():
            result = tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_123",
                tool_name="subtract",
                input_data=input_data,
            )

            assert result.input == input_data

    def test_create_tool_call_sets_pending_status(self, app, tool_call_repo, sample_message):
        """Test that create sets status to 'pending'."""
        with app.app_context():
            result = tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_123",
                tool_name="add",
                input_data={"a": 1, "b": 2},
            )

            assert result.status == "pending"

    def test_create_tool_call_sets_started_at(self, app, tool_call_repo, sample_message):
        """Test that create sets started_at timestamp."""
        with app.app_context():
            result = tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_123",
                tool_name="add",
                input_data={"a": 1, "b": 2},
            )

            assert result.started_at is not None


class TestToolCallRepositoryFindByMessageId:
    """Tests for ToolCallRepository.find_by_message_id method."""

    def test_find_by_message_id_returns_empty_when_none(self, app, tool_call_repo, sample_message):
        """Test that find_by_message_id returns empty list when no tool calls exist."""
        with app.app_context():
            result = tool_call_repo.find_by_message_id(sample_message)

            assert len(result) == 0

    def test_find_by_message_id_returns_single_tool_call(self, app, tool_call_repo, sample_message):
        """Test that find_by_message_id returns a single tool call."""
        with app.app_context():
            tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_1",
                tool_name="add",
                input_data={"a": 1, "b": 2},
            )

            result = tool_call_repo.find_by_message_id(sample_message)

            assert len(result) == 1
            assert result[0].tool_call_id == "tool_call_1"

    def test_find_by_message_id_returns_multiple_tool_calls(self, app, tool_call_repo, sample_message):
        """Test that find_by_message_id returns multiple tool calls."""
        with app.app_context():
            tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_1",
                tool_name="add",
                input_data={"a": 1, "b": 2},
            )
            tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_2",
                tool_name="multiply",
                input_data={"a": 3, "b": 4},
            )

            result = tool_call_repo.find_by_message_id(sample_message)

            assert len(result) == 2

    def test_find_by_message_id_returns_only_matching_message(self, app, tool_call_repo, sample_message, test_user):
        """Test that find_by_message_id only returns tool calls for the specified message."""
        from app.database import get_session
        from app.models.conversation import Conversation
        from app.models.message import Message

        with app.app_context():
            session = get_session()

            # Create another message
            conversation = Conversation(user_id=test_user, title="Another")
            session.add(conversation)
            session.flush()
            other_message = Message(conversation_id=conversation.id, role="assistant", content="Other")
            session.add(other_message)
            session.commit()

            # Create tool calls for both messages
            tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_1",
                tool_name="add",
                input_data={"a": 1, "b": 2},
            )
            tool_call_repo.create(
                message_id=other_message.id,
                tool_call_id="tool_call_2",
                tool_name="multiply",
                input_data={"a": 3, "b": 4},
            )

            result = tool_call_repo.find_by_message_id(sample_message)

            assert len(result) == 1
            assert result[0].tool_call_id == "tool_call_1"


class TestToolCallRepositoryUpdateCompleted:
    """Tests for ToolCallRepository.update_completed method."""

    def test_update_completed_success_sets_output(self, app, tool_call_repo, sample_message):
        """Test that update_completed sets output for successful execution."""
        with app.app_context():
            tool_call = tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_123",
                tool_name="add",
                input_data={"a": 1, "b": 2},
            )

            result = tool_call_repo.update_completed(
                tool_call_id="tool_call_123",
                output="3",
                error=None,
                status="success",
            )

            assert result is not None
            assert result.output == "3"

    def test_update_completed_success_sets_status(self, app, tool_call_repo, sample_message):
        """Test that update_completed sets status to 'success'."""
        with app.app_context():
            tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_123",
                tool_name="add",
                input_data={"a": 1, "b": 2},
            )

            result = tool_call_repo.update_completed(
                tool_call_id="tool_call_123",
                output="3",
                error=None,
                status="success",
            )

            assert result.status == "success"

    def test_update_completed_error_sets_error_message(self, app, tool_call_repo, sample_message):
        """Test that update_completed sets error message for failed execution."""
        with app.app_context():
            tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_123",
                tool_name="divide",
                input_data={"a": 1, "b": 0},
            )

            result = tool_call_repo.update_completed(
                tool_call_id="tool_call_123",
                output=None,
                error="Cannot divide by zero",
                status="error",
            )

            assert result.error == "Cannot divide by zero"

    def test_update_completed_error_sets_status(self, app, tool_call_repo, sample_message):
        """Test that update_completed sets status to 'error'."""
        with app.app_context():
            tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_123",
                tool_name="divide",
                input_data={"a": 1, "b": 0},
            )

            result = tool_call_repo.update_completed(
                tool_call_id="tool_call_123",
                output=None,
                error="Cannot divide by zero",
                status="error",
            )

            assert result.status == "error"

    def test_update_completed_sets_completed_at(self, app, tool_call_repo, sample_message):
        """Test that update_completed sets completed_at timestamp."""
        with app.app_context():
            tool_call_repo.create(
                message_id=sample_message,
                tool_call_id="tool_call_123",
                tool_name="add",
                input_data={"a": 1, "b": 2},
            )

            result = tool_call_repo.update_completed(
                tool_call_id="tool_call_123",
                output="3",
                error=None,
                status="success",
            )

            assert result.completed_at is not None

    def test_update_completed_returns_none_for_unknown_id(self, app, tool_call_repo, sample_message):
        """Test that update_completed returns None for unknown tool_call_id."""
        with app.app_context():
            result = tool_call_repo.update_completed(
                tool_call_id="nonexistent_id",
                output="3",
                error=None,
                status="success",
            )

            assert result is None
