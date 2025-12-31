"""Tests for ConversationService (conversation business logic)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import ConversationAccessDeniedError, ConversationNotFoundError
from app.repositories.tool_call_repository import ToolCallData
from app.services.agent_service import MessageCompleteEvent, MessageMetadataEvent, RetryEvent, TextDeltaEvent, ToolCallEvent, ToolResultEvent
from app.services.conversation_service import AgentStreamingResult, ConversationService
from app.services.metadata_service import StreamingResult


@pytest.fixture
def conversation_service(app):
    """Create ConversationService instance with test database session."""
    from app.database import get_session

    with app.app_context():
        session = get_session()
        # Create with mock agent service to avoid external API calls
        mock_agent = MagicMock()
        mock_agent.generate_title.return_value = "Test Title"
        yield ConversationService(session, agent_service=mock_agent), session


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

        user_msg = Message(conversation_id=conversation.id, role="user", content="Hello")
        assistant_msg = Message(conversation_id=conversation.id, role="assistant", content="Hi there!")
        session.add_all([user_msg, assistant_msg])
        session.commit()

        conv_id = conversation.id
        conv_uuid = conversation.uuid
        session.expunge_all()

    return {"id": conv_id, "uuid": conv_uuid, "user_id": test_user}


class TestConversationServiceInit:
    """Tests for ConversationService initialization."""

    def test_init_with_agent_service(self, app):
        """Test initialization with provided agent service."""
        from app.database import get_session

        with app.app_context():
            session = get_session()
            mock_agent = MagicMock()
            service = ConversationService(session, agent_service=mock_agent)

            assert service._agent_service is mock_agent

    def test_agent_service_lazy_creation(self, app):
        """Test that agent service is created lazily when accessed."""
        from app.database import get_session

        with app.app_context():
            session = get_session()
            service = ConversationService(session)

            assert service._agent_service is None

            with patch("app.services.conversation_service.AgentService") as mock_class:
                mock_instance = MagicMock()
                mock_class.return_value = mock_instance
                agent = service.agent_service

                assert agent is mock_instance
                mock_class.assert_called_once()


class TestListConversations:
    """Tests for ConversationService.list_conversations method."""

    def test_list_conversations_empty(self, app, conversation_service, test_user):
        """Test listing conversations when user has none."""
        service, session = conversation_service
        result = service.list_conversations(test_user)

        assert len(result.conversations) == 0
        assert result.meta.total == 0
        assert result.meta.page == 1

    def test_list_conversations_with_data(self, app, conversation_service, test_user):
        """Test listing conversations with existing data."""
        service, session = conversation_service

        # Create conversations directly
        from app.models.conversation import Conversation

        for i in range(3):
            conv = Conversation(user_id=test_user, title=f"Conversation {i}")
            session.add(conv)
        session.flush()

        result = service.list_conversations(test_user)

        assert len(result.conversations) == 3
        assert result.meta.total == 3

    def test_list_conversations_pagination(self, app, conversation_service, test_user):
        """Test pagination in list_conversations."""
        service, session = conversation_service

        from app.models.conversation import Conversation

        for i in range(5):
            conv = Conversation(user_id=test_user, title=f"Conversation {i}")
            session.add(conv)
        session.flush()

        result = service.list_conversations(test_user, page=1, per_page=2)

        assert len(result.conversations) == 2
        assert result.meta.total == 5
        assert result.meta.total_pages == 3

    def test_list_conversations_clamps_per_page(self, app, conversation_service, test_user):
        """Test that per_page is clamped to valid range."""
        service, session = conversation_service

        # Test with too small value
        result = service.list_conversations(test_user, per_page=0)
        assert result.meta.per_page >= 1

        # Test with too large value
        result = service.list_conversations(test_user, per_page=1000)
        assert result.meta.per_page <= 100


class TestGetConversation:
    """Tests for ConversationService.get_conversation method."""

    def test_get_conversation_success(self, app, conversation_service, conversation_with_messages):
        """Test getting a conversation successfully."""
        service, session = conversation_service
        result = service.get_conversation(
            conversation_with_messages["uuid"],
            conversation_with_messages["user_id"],
        )

        assert result.conversation.uuid == conversation_with_messages["uuid"]
        assert len(result.messages) == 2

    def test_get_conversation_not_found(self, app, conversation_service, test_user):
        """Test getting non-existent conversation raises error."""
        service, session = conversation_service

        with pytest.raises(ConversationNotFoundError):
            service.get_conversation("nonexistent-uuid", test_user)

    def test_get_conversation_access_denied(self, app, conversation_service, conversation_with_messages):
        """Test accessing another user's conversation raises error."""
        service, session = conversation_service

        with pytest.raises(ConversationAccessDeniedError):
            service.get_conversation(conversation_with_messages["uuid"], 99999)


class TestCreateConversation:
    """Tests for ConversationService.create_conversation method."""

    def test_create_conversation_success(self, app, conversation_service, test_user):
        """Test creating a conversation successfully."""
        service, session = conversation_service
        result = service.create_conversation(test_user, "Hello, AI!")

        assert result.conversation.title == "Test Title"
        assert result.message.content == "Hello, AI!"
        assert result.message.role == "user"

    def test_create_conversation_generates_title(self, app, conversation_service, test_user):
        """Test that title is generated from first message."""
        service, session = conversation_service
        service.create_conversation(test_user, "My test message")

        service._agent_service.generate_title.assert_called_once_with("My test message")


class TestDeleteConversation:
    """Tests for ConversationService.delete_conversation method."""

    def test_delete_conversation_success(self, app, conversation_service, conversation_with_messages):
        """Test deleting a conversation successfully."""
        service, session = conversation_service
        service.delete_conversation(
            conversation_with_messages["uuid"],
            conversation_with_messages["user_id"],
        )
        session.commit()

        # Verify deletion by checking repository directly
        result = service.conversation_repo.find_by_uuid(conversation_with_messages["uuid"])
        assert result is None

    def test_delete_conversation_not_found(self, app, conversation_service, test_user):
        """Test deleting non-existent conversation raises error."""
        service, session = conversation_service

        with pytest.raises(ConversationNotFoundError):
            service.delete_conversation("nonexistent-uuid", test_user)


class TestValidateConversationAccess:
    """Tests for ConversationService.validate_conversation_access method."""

    def test_validate_access_success(self, app, conversation_service, conversation_with_messages):
        """Test successful access validation."""
        service, session = conversation_service
        result = service.validate_conversation_access(
            conversation_with_messages["uuid"],
            conversation_with_messages["user_id"],
        )

        assert result.uuid == conversation_with_messages["uuid"]

    def test_validate_access_with_messages(self, app, conversation_service, conversation_with_messages):
        """Test access validation with messages loaded."""
        service, session = conversation_service
        result = service.validate_conversation_access(
            conversation_with_messages["uuid"],
            conversation_with_messages["user_id"],
            with_messages=True,
        )

        assert len(result.messages) == 2


class TestBuildMessageHistory:
    """Tests for ConversationService._build_message_history method."""

    def test_build_message_history_empty(self, app, conversation_service):
        """Test building history with no existing messages."""
        service, session = conversation_service
        result = service._build_message_history([], "New message")

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "New message"

    def test_build_message_history_with_existing(self, app, conversation_service):
        """Test building history with existing messages."""
        service, session = conversation_service

        existing = [
            MagicMock(role="user", content="First"),
            MagicMock(role="assistant", content="Response"),
        ]
        result = service._build_message_history(existing, "Second")

        assert len(result) == 3
        assert result[0]["content"] == "First"
        assert result[1]["content"] == "Response"
        assert result[2]["content"] == "Second"


class TestProcessAgentEvent:
    """Tests for ConversationService._process_agent_event method."""

    def test_process_tool_call_event(self, app, conversation_service):
        """Test processing ToolCallEvent buffers tool call data."""
        service, session = conversation_service

        event = ToolCallEvent(
            tool_call_id="tc_123",
            tool_name="calculator",
            input={"a": 1, "b": 2},
        )
        tool_call_buffer: dict[str, ToolCallData] = {}
        streaming_event, text = service._process_agent_event(event, tool_call_buffer)

        assert streaming_event is not None
        assert streaming_event[0] == "tool_call_start"
        assert streaming_event[1]["tool_call_id"] == "tc_123"
        assert text is None

        # Verify tool call was buffered
        assert "tc_123" in tool_call_buffer
        assert tool_call_buffer["tc_123"].tool_name == "calculator"
        assert tool_call_buffer["tc_123"].input_data == {"a": 1, "b": 2}
        assert tool_call_buffer["tc_123"].status == "pending"

    def test_process_tool_result_event(self, app, conversation_service):
        """Test processing ToolResultEvent updates buffered tool call."""
        service, session = conversation_service

        # First buffer a tool call
        tool_call_buffer: dict[str, ToolCallData] = {
            "tc_123": ToolCallData(
                tool_call_id="tc_123",
                tool_name="calculator",
                input_data={"a": 1, "b": 2},
            )
        }

        event = ToolResultEvent(
            tool_call_id="tc_123",
            output="3",
            error=None,
        )
        streaming_event, text = service._process_agent_event(event, tool_call_buffer)

        assert streaming_event is not None
        assert streaming_event[0] == "tool_call_end"
        assert streaming_event[1]["output"] == "3"
        assert text is None

        # Verify buffered tool call was updated
        assert tool_call_buffer["tc_123"].output == "3"
        assert tool_call_buffer["tc_123"].status == "success"
        assert tool_call_buffer["tc_123"].completed_at is not None

    def test_process_tool_result_event_with_error(self, app, conversation_service):
        """Test processing ToolResultEvent with error updates buffered tool call."""
        service, session = conversation_service

        tool_call_buffer: dict[str, ToolCallData] = {
            "tc_123": ToolCallData(
                tool_call_id="tc_123",
                tool_name="divide",
                input_data={"a": 1, "b": 0},
            )
        }

        event = ToolResultEvent(
            tool_call_id="tc_123",
            output=None,
            error="Cannot divide by zero",
        )
        streaming_event, text = service._process_agent_event(event, tool_call_buffer)

        assert streaming_event[1]["error"] == "Cannot divide by zero"
        assert tool_call_buffer["tc_123"].status == "error"
        assert tool_call_buffer["tc_123"].error == "Cannot divide by zero"

    def test_process_text_delta_event(self, app, conversation_service):
        """Test processing TextDeltaEvent."""
        service, session = conversation_service

        event = TextDeltaEvent(delta="Hello")
        tool_call_buffer: dict[str, ToolCallData] = {}
        streaming_event, text = service._process_agent_event(event, tool_call_buffer)

        assert streaming_event is not None
        assert streaming_event[0] == "delta"
        assert streaming_event[1]["delta"] == "Hello"
        assert text == "Hello"

    def test_process_message_complete_event(self, app, conversation_service):
        """Test processing MessageCompleteEvent."""
        service, session = conversation_service

        event = MessageCompleteEvent(content="Full response")
        tool_call_buffer: dict[str, ToolCallData] = {}
        streaming_event, text = service._process_agent_event(event, tool_call_buffer)

        assert streaming_event is None
        assert text == "Full response"

    def test_process_retry_event(self, app, conversation_service):
        """Test processing RetryEvent."""
        service, session = conversation_service

        event = RetryEvent(
            attempt=1,
            max_attempts=3,
            error_type="rate_limit",
            delay=1.0,
        )
        tool_call_buffer: dict[str, ToolCallData] = {}
        streaming_event, text = service._process_agent_event(event, tool_call_buffer)

        assert streaming_event is not None
        assert streaming_event[0] == "retry"
        assert streaming_event[1]["attempt"] == 1
        assert text is None


class TestFinalizeStreamingResponse:
    """Tests for ConversationService._finalize_streaming_response method."""

    def test_finalize_response_updates_message(self, app, conversation_service, conversation_with_messages):
        """Test that finalize updates the assistant message."""
        service, session = conversation_service

        from app.models.message import Message

        msg = Message(
            conversation_id=conversation_with_messages["id"],
            role="assistant",
            content="",
        )
        session.add(msg)
        session.flush()

        from app.models.conversation import Conversation

        conversation = session.get(Conversation, conversation_with_messages["id"])

        streaming_result = StreamingResult(
            content="Final response",
            input_tokens=100,
            output_tokens=50,
            model="claude-3",
            response_time_ms=1000,
            cost_usd=0.001,
        )
        result = AgentStreamingResult(streaming_result=streaming_result)

        end_data = service._finalize_streaming_response(msg, conversation, result)

        assert msg.content == "Final response"
        assert msg.input_tokens == 100
        assert msg.output_tokens == 50
        assert end_data["content"] == "Final response"

    def test_finalize_response_handles_zero_values(self, app, conversation_service, conversation_with_messages):
        """Test that finalize handles zero metadata values correctly."""
        service, session = conversation_service

        from app.models.message import Message

        msg = Message(
            conversation_id=conversation_with_messages["id"],
            role="assistant",
            content="",
        )
        session.add(msg)
        session.flush()

        from app.models.conversation import Conversation

        conversation = session.get(Conversation, conversation_with_messages["id"])

        streaming_result = StreamingResult(
            content="Response",
            input_tokens=0,
            output_tokens=0,
            model="",
            response_time_ms=0,
            cost_usd=0.0,
        )
        result = AgentStreamingResult(streaming_result=streaming_result)

        service._finalize_streaming_response(msg, conversation, result)

        # Zero/empty values should be None in message
        assert msg.input_tokens is None
        assert msg.output_tokens is None
        assert msg.model is None

    def test_finalize_response_batch_inserts_tool_calls(self, app, conversation_service, conversation_with_messages):
        """Test that finalize batch inserts buffered tool calls."""
        service, session = conversation_service

        from app.models.message import Message

        msg = Message(
            conversation_id=conversation_with_messages["id"],
            role="assistant",
            content="",
        )
        session.add(msg)
        session.flush()

        from app.models.conversation import Conversation

        conversation = session.get(Conversation, conversation_with_messages["id"])

        # Create tool call data
        tool_calls = [
            ToolCallData(
                tool_call_id="tc_1",
                tool_name="add",
                input_data={"a": 1, "b": 2},
            ),
            ToolCallData(
                tool_call_id="tc_2",
                tool_name="multiply",
                input_data={"a": 3, "b": 4},
            ),
        ]
        tool_calls[0].complete(output="3")
        tool_calls[1].complete(output="12")

        streaming_result = StreamingResult(
            content="Result: 3 and 12",
            input_tokens=50,
            output_tokens=25,
            model="claude-3",
            response_time_ms=500,
            cost_usd=0.001,
        )
        result = AgentStreamingResult(streaming_result=streaming_result, tool_calls=tool_calls)

        end_data = service._finalize_streaming_response(msg, conversation, result)

        # Verify tool calls were created in the database
        assert len(end_data["tool_calls"]) == 2
        assert end_data["tool_calls"][0]["tool_call_id"] == "tc_1"
        assert end_data["tool_calls"][1]["tool_call_id"] == "tc_2"

        # Verify tool calls can be retrieved from the database
        db_tool_calls = service.tool_call_repo.find_by_message_id(msg.id)
        assert len(db_tool_calls) == 2


class TestStreamingMethods:
    """Tests for streaming methods in ConversationService."""

    def test_create_conversation_streaming_yields_created_event(self, app, conversation_service, test_user):
        """Test that create_conversation_streaming yields created event first."""
        service, session = conversation_service

        # Mock agent response
        service._agent_service.generate_response.return_value = iter(
            [
                TextDeltaEvent(delta="Hello"),
                MessageCompleteEvent(content="Hello"),
                MessageMetadataEvent(input_tokens=10, output_tokens=5, model="claude-3", response_time_ms=100),
            ]
        )

        events = list(service.create_conversation_streaming(test_user, "Hi"))

        assert len(events) >= 2
        assert events[0][0] == "created"
        assert "conversation" in events[0][1]
        assert "user_message_id" in events[0][1]

    def test_create_conversation_streaming_yields_end_event(self, app, conversation_service, test_user):
        """Test that create_conversation_streaming yields end event last."""
        service, session = conversation_service

        service._agent_service.generate_response.return_value = iter(
            [
                TextDeltaEvent(delta="Hi"),
                MessageCompleteEvent(content="Hi"),
                MessageMetadataEvent(input_tokens=10, output_tokens=5, model="claude-3", response_time_ms=100),
            ]
        )

        events = list(service.create_conversation_streaming(test_user, "Hello"))

        assert events[-1][0] == "end"
        assert "assistant_message_id" in events[-1][1]
        assert "content" in events[-1][1]

    def test_send_message_streaming_yields_start_event(self, app, conversation_service, conversation_with_messages):
        """Test that send_message_streaming yields start event first."""
        service, session = conversation_service

        service._agent_service.generate_response.return_value = iter(
            [
                TextDeltaEvent(delta="Response"),
                MessageCompleteEvent(content="Response"),
                MessageMetadataEvent(input_tokens=20, output_tokens=10, model="claude-3", response_time_ms=200),
            ]
        )

        events = list(
            service.send_message_streaming(
                conversation_with_messages["uuid"],
                conversation_with_messages["user_id"],
                "Another message",
            )
        )

        assert events[0][0] == "start"
        assert "user_message_id" in events[0][1]

    def test_send_message_streaming_yields_delta_events(self, app, conversation_service, conversation_with_messages):
        """Test that send_message_streaming yields delta events."""
        service, session = conversation_service

        service._agent_service.generate_response.return_value = iter(
            [
                TextDeltaEvent(delta="Part 1"),
                TextDeltaEvent(delta=" Part 2"),
                MessageCompleteEvent(content="Part 1 Part 2"),
                MessageMetadataEvent(input_tokens=20, output_tokens=10, model="claude-3", response_time_ms=200),
            ]
        )

        events = list(
            service.send_message_streaming(
                conversation_with_messages["uuid"],
                conversation_with_messages["user_id"],
                "Test",
            )
        )

        delta_events = [e for e in events if e[0] == "delta"]
        assert len(delta_events) == 2
        assert delta_events[0][1]["delta"] == "Part 1"
        assert delta_events[1][1]["delta"] == " Part 2"

    def test_send_message_streaming_access_denied(self, app, conversation_service, conversation_with_messages):
        """Test that send_message_streaming raises error for wrong user."""
        service, session = conversation_service

        with pytest.raises(ConversationAccessDeniedError):
            list(
                service.send_message_streaming(
                    conversation_with_messages["uuid"],
                    99999,
                    "Test",
                )
            )


class TestStreamAgentResponse:
    """Tests for ConversationService._stream_agent_response method."""

    def test_stream_agent_response_returns_result(self, app, conversation_service):
        """Test that _stream_agent_response returns AgentStreamingResult."""
        service, session = conversation_service

        service._agent_service.generate_response.return_value = iter(
            [
                TextDeltaEvent(delta="Test"),
                MessageCompleteEvent(content="Test"),
                MessageMetadataEvent(input_tokens=50, output_tokens=25, model="claude-3", response_time_ms=500),
            ]
        )

        tool_call_buffer: dict[str, ToolCallData] = {}
        gen = service._stream_agent_response([{"role": "user", "content": "Hi"}], tool_call_buffer)

        # Consume generator to get result
        result = None
        try:
            while True:
                next(gen)
        except StopIteration as e:
            result = e.value

        assert isinstance(result, AgentStreamingResult)
        assert result.streaming_result.content == "Test"
        assert result.streaming_result.input_tokens == 50
        assert result.streaming_result.output_tokens == 25
        assert result.tool_calls == []

    def test_stream_agent_response_yields_events(self, app, conversation_service):
        """Test that _stream_agent_response yields streaming events."""
        service, session = conversation_service

        service._agent_service.generate_response.return_value = iter(
            [
                TextDeltaEvent(delta="Hello"),
                TextDeltaEvent(delta=" World"),
                MessageCompleteEvent(content="Hello World"),
                MessageMetadataEvent(input_tokens=10, output_tokens=5, model="claude-3", response_time_ms=100),
            ]
        )

        tool_call_buffer: dict[str, ToolCallData] = {}
        gen = service._stream_agent_response([{"role": "user", "content": "Hi"}], tool_call_buffer)

        events = []
        try:
            while True:
                events.append(next(gen))
        except StopIteration:
            pass

        assert len(events) == 2  # Two delta events
        assert events[0][0] == "delta"
        assert events[1][0] == "delta"

    def test_stream_agent_response_buffers_tool_calls(self, app, conversation_service):
        """Test that _stream_agent_response buffers tool calls."""
        service, session = conversation_service

        service._agent_service.generate_response.return_value = iter(
            [
                ToolCallEvent(tool_call_id="tc_1", tool_name="add", input={"a": 1, "b": 2}),
                ToolResultEvent(tool_call_id="tc_1", output="3", error=None),
                TextDeltaEvent(delta="Result: 3"),
                MessageCompleteEvent(content="Result: 3"),
                MessageMetadataEvent(input_tokens=50, output_tokens=25, model="claude-3", response_time_ms=500),
            ]
        )

        tool_call_buffer: dict[str, ToolCallData] = {}
        gen = service._stream_agent_response([{"role": "user", "content": "Add 1+2"}], tool_call_buffer)

        # Consume generator to get result
        events = []
        result = None
        try:
            while True:
                events.append(next(gen))
        except StopIteration as e:
            result = e.value

        # Verify events were yielded
        assert len(events) == 3  # tool_call_start, tool_call_end, delta
        assert events[0][0] == "tool_call_start"
        assert events[1][0] == "tool_call_end"
        assert events[2][0] == "delta"

        # Verify tool calls were buffered
        assert isinstance(result, AgentStreamingResult)
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].tool_call_id == "tc_1"
        assert result.tool_calls[0].output == "3"
        assert result.tool_calls[0].status == "success"

    def test_stream_agent_response_populates_buffer(self, app, conversation_service):
        """Test that _stream_agent_response populates the provided buffer."""
        service, session = conversation_service

        service._agent_service.generate_response.return_value = iter(
            [
                ToolCallEvent(tool_call_id="tc_1", tool_name="add", input={"a": 1, "b": 2}),
                ToolResultEvent(tool_call_id="tc_1", output="3", error=None),
                MessageCompleteEvent(content="Done"),
                MessageMetadataEvent(input_tokens=10, output_tokens=5, model="claude-3", response_time_ms=100),
            ]
        )

        tool_call_buffer: dict[str, ToolCallData] = {}
        gen = service._stream_agent_response([{"role": "user", "content": "Hi"}], tool_call_buffer)

        # Partially consume generator (simulate interruption)
        next(gen)  # tool_call_start
        next(gen)  # tool_call_end

        # Verify buffer was populated even without completing the generator
        assert "tc_1" in tool_call_buffer
        assert tool_call_buffer["tc_1"].tool_name == "add"
        assert tool_call_buffer["tc_1"].status == "success"


class TestStreamingAbortHandling:
    """Tests for streaming abort handling - tool calls should persist on interruption."""

    def test_send_message_streaming_persists_tool_calls_on_abort(self, app, conversation_service, conversation_with_messages):
        """Test that tool calls are persisted when streaming is interrupted."""
        service, session = conversation_service

        # Mock agent to raise exception after yielding tool call events
        def generate_response_with_error(*args, **kwargs):
            yield ToolCallEvent(tool_call_id="tc_abort_1", tool_name="add", input={"a": 1, "b": 2})
            yield ToolResultEvent(tool_call_id="tc_abort_1", output="3", error=None)
            raise RuntimeError("Simulated API error")

        service._agent_service.generate_response = generate_response_with_error

        # Start streaming
        gen = service.send_message_streaming(
            uuid=conversation_with_messages["uuid"],
            user_id=conversation_with_messages["user_id"],
            content="Test",
        )

        # Consume events until error
        events = []
        try:
            for event in gen:
                events.append(event)
        except RuntimeError:
            pass  # Expected

        # Verify tool calls were persisted despite the error
        # Find the assistant message that was created
        from app.models.message import Message

        assistant_messages = (
            session.query(Message)
            .filter(
                Message.conversation_id == conversation_with_messages["id"],
                Message.role == "assistant",
            )
            .all()
        )
        assert len(assistant_messages) >= 1
        latest_assistant = assistant_messages[-1]

        # Verify tool call was persisted
        tool_calls = service.tool_call_repo.find_by_message_id(latest_assistant.id)
        assert len(tool_calls) == 1
        assert tool_calls[0].tool_call_id == "tc_abort_1"
        assert tool_calls[0].status == "success"


class TestStreamingResultDataclass:
    """Tests for StreamingResult dataclass."""

    def test_streaming_result_creation(self):
        """Test creating StreamingResult with all fields."""
        result = StreamingResult(
            content="Test content",
            input_tokens=100,
            output_tokens=50,
            model="claude-3",
            response_time_ms=1500,
            cost_usd=0.005,
        )

        assert result.content == "Test content"
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.model == "claude-3"
        assert result.response_time_ms == 1500
        assert result.cost_usd == 0.005

    def test_streaming_result_with_zero_values(self):
        """Test creating StreamingResult with zero values."""
        result = StreamingResult(
            content="",
            input_tokens=0,
            output_tokens=0,
            model="",
            response_time_ms=0,
            cost_usd=0.0,
        )

        assert result.content == ""
        assert result.input_tokens == 0
