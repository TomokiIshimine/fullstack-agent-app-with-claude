"""Tests for ToolCallRepository."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models.tool_call import ToolCall
from app.repositories.tool_call_repository import ToolCallData, ToolCallRepository


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


class TestToolCallData:
    """Tests for ToolCallData dataclass."""

    def test_create_with_defaults(self):
        """Test creating ToolCallData with default values."""
        data = ToolCallData(
            tool_call_id="call_123",
            tool_name="add",
            input_data={"a": 1, "b": 2},
        )

        assert data.tool_call_id == "call_123"
        assert data.tool_name == "add"
        assert data.input_data == {"a": 1, "b": 2}
        assert data.status == "pending"
        assert data.output is None
        assert data.error is None
        assert data.started_at is not None
        assert data.completed_at is None

    def test_complete_with_output(self):
        """Test completing ToolCallData with successful output."""
        data = ToolCallData(
            tool_call_id="call_123",
            tool_name="add",
            input_data={"a": 1, "b": 2},
        )

        data.complete(output="3")

        assert data.status == "success"
        assert data.output == "3"
        assert data.error is None
        assert data.completed_at is not None

    def test_complete_with_error(self):
        """Test completing ToolCallData with error."""
        data = ToolCallData(
            tool_call_id="call_123",
            tool_name="divide",
            input_data={"a": 1, "b": 0},
        )

        data.complete(error="Cannot divide by zero")

        assert data.status == "error"
        assert data.output is None
        assert data.error == "Cannot divide by zero"
        assert data.completed_at is not None


class TestToolCallRepositoryCreateBatch:
    """Tests for ToolCallRepository.create_batch method."""

    def test_create_batch_with_empty_list_returns_empty(self, app, tool_call_repo, sample_message):
        """Test that create_batch with empty list returns empty list."""
        with app.app_context():
            result = tool_call_repo.create_batch(
                message_id=sample_message,
                tool_calls=[],
            )

            assert result == []

    def test_create_batch_with_single_tool_call(self, app, tool_call_repo, sample_message):
        """Test that create_batch creates a single tool call."""
        with app.app_context():
            tool_call_data = ToolCallData(
                tool_call_id="call_123",
                tool_name="add",
                input_data={"a": 1, "b": 2},
            )
            tool_call_data.complete(output="3")

            result = tool_call_repo.create_batch(
                message_id=sample_message,
                tool_calls=[tool_call_data],
            )

            assert len(result) == 1
            assert isinstance(result[0], ToolCall)
            assert result[0].tool_call_id == "call_123"
            assert result[0].tool_name == "add"
            assert result[0].input == {"a": 1, "b": 2}
            assert result[0].output == "3"
            assert result[0].status == "success"

    def test_create_batch_with_multiple_tool_calls(self, app, tool_call_repo, sample_message):
        """Test that create_batch creates multiple tool calls."""
        with app.app_context():
            tool_calls = [
                ToolCallData(
                    tool_call_id="call_1",
                    tool_name="add",
                    input_data={"a": 1, "b": 2},
                ),
                ToolCallData(
                    tool_call_id="call_2",
                    tool_name="multiply",
                    input_data={"a": 3, "b": 4},
                ),
            ]
            tool_calls[0].complete(output="3")
            tool_calls[1].complete(output="12")

            result = tool_call_repo.create_batch(
                message_id=sample_message,
                tool_calls=tool_calls,
            )

            assert len(result) == 2
            assert result[0].tool_call_id == "call_1"
            assert result[0].output == "3"
            assert result[1].tool_call_id == "call_2"
            assert result[1].output == "12"

    def test_create_batch_preserves_timestamps(self, app, tool_call_repo, sample_message):
        """Test that create_batch preserves started_at and completed_at timestamps."""
        with app.app_context():
            started_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            tool_call_data = ToolCallData(
                tool_call_id="call_123",
                tool_name="add",
                input_data={"a": 1, "b": 2},
                started_at=started_at,
            )
            tool_call_data.complete(output="3")

            result = tool_call_repo.create_batch(
                message_id=sample_message,
                tool_calls=[tool_call_data],
            )

            assert result[0].started_at == started_at
            assert result[0].completed_at is not None

    def test_create_batch_with_error_status(self, app, tool_call_repo, sample_message):
        """Test that create_batch handles error status correctly."""
        with app.app_context():
            tool_call_data = ToolCallData(
                tool_call_id="call_123",
                tool_name="divide",
                input_data={"a": 1, "b": 0},
            )
            tool_call_data.complete(error="Cannot divide by zero")

            result = tool_call_repo.create_batch(
                message_id=sample_message,
                tool_calls=[tool_call_data],
            )

            assert result[0].status == "error"
            assert result[0].error == "Cannot divide by zero"
            assert result[0].output is None

    def test_create_batch_with_pending_status(self, app, tool_call_repo, sample_message):
        """Test that create_batch handles pending tool calls correctly."""
        with app.app_context():
            tool_call_data = ToolCallData(
                tool_call_id="call_123",
                tool_name="add",
                input_data={"a": 1, "b": 2},
            )
            # Don't call complete() - keep pending status

            result = tool_call_repo.create_batch(
                message_id=sample_message,
                tool_calls=[tool_call_data],
            )

            assert result[0].status == "pending"
            assert result[0].output is None
            assert result[0].completed_at is None

    def test_create_batch_single_flush(self, app, tool_call_repo, sample_message):
        """Test that create_batch performs only one flush for multiple tool calls."""
        with app.app_context():
            tool_calls = [
                ToolCallData(
                    tool_call_id=f"call_{i}",
                    tool_name="add",
                    input_data={"a": i, "b": i},
                )
                for i in range(5)
            ]
            for tc in tool_calls:
                tc.complete(output=str(tc.input_data["a"] * 2))

            result = tool_call_repo.create_batch(
                message_id=sample_message,
                tool_calls=tool_calls,
            )

            # All should have been created
            assert len(result) == 5

            # All should have valid IDs (meaning flush was successful)
            for tc in result:
                assert tc.id is not None

    def test_create_batch_can_be_retrieved_by_find(self, app, tool_call_repo, sample_message):
        """Test that batch-created tool calls can be retrieved by find_by_message_id."""
        with app.app_context():
            tool_calls = [
                ToolCallData(
                    tool_call_id="call_1",
                    tool_name="add",
                    input_data={"a": 1, "b": 2},
                ),
                ToolCallData(
                    tool_call_id="call_2",
                    tool_name="multiply",
                    input_data={"a": 3, "b": 4},
                ),
            ]
            for tc in tool_calls:
                tc.complete(output="result")

            tool_call_repo.create_batch(
                message_id=sample_message,
                tool_calls=tool_calls,
            )

            # Retrieve using find_by_message_id
            found = tool_call_repo.find_by_message_id(sample_message)

            assert len(found) == 2
            tool_call_ids = {tc.tool_call_id for tc in found}
            assert tool_call_ids == {"call_1", "call_2"}
