"""Tests for AgentService (LangGraph ReAct agent integration)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from anthropic import APIConnectionError, APIStatusError, RateLimitError
from httpx import Request, Response
from langchain_core.messages import AIMessageChunk, ToolMessage

from app.constants.error_types import LLMErrorType
from app.core.exceptions import LLMConnectionError, LLMContextLengthError, LLMRateLimitError, LLMStreamError, ProviderNotFoundError
from app.providers import LLMConfig, create_provider
from app.services.agent_service import AgentService, MessageCompleteEvent, RetryEvent, TextDeltaEvent, ToolCallEvent, ToolResultEvent
from app.tools import ToolRegistry


class TestAgentServiceInit:
    """Tests for AgentService initialization."""

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_init_with_default_provider(self, mock_create_provider, mock_create_agent):
        """Test initialization with default provider from environment."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-sonnet-4-5-20250929"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()

        assert service.provider_name == "anthropic"
        mock_create_provider.assert_called_once()
        mock_create_agent.assert_called_once()

    @patch("app.services.agent_service.create_react_agent")
    def test_init_with_provider(self, mock_create_agent):
        """Test initialization with LLM provider instance."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-opus-4"
        mock_provider.config.max_tokens = 8192

        service = AgentService(provider=mock_provider)

        assert service.provider_name == "anthropic"
        assert service.model_name == "claude-opus-4"
        assert service.max_tokens == 8192
        assert service.provider is mock_provider

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_init_with_custom_tool_registry(self, mock_create_provider, mock_create_agent):
        """Test initialization with custom tool registry."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-sonnet-4-5-20250929"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        registry = ToolRegistry()
        service = AgentService(tool_registry=registry)

        assert service.tools == []

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_init_registers_default_tools(self, mock_create_provider, mock_create_agent):
        """Test that initialization registers default tools from global registry."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-sonnet-4-5-20250929"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()

        # Default registry should have calculator tools
        assert len(service.tools) > 0

    def test_init_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises ProviderNotFoundError."""
        config = LLMConfig(provider="unsupported_provider", model="test-model")

        with pytest.raises(ProviderNotFoundError, match="サポートされていないLLMプロバイダー"):
            create_provider(config)

    @patch("app.services.agent_service.create_react_agent")
    def test_init_with_custom_system_prompt(self, mock_create_agent):
        """Test initialization with custom system prompt."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0

        custom_prompt = "You are a custom assistant."
        service = AgentService(provider=mock_provider, system_prompt=custom_prompt)

        assert service._system_prompt == custom_prompt
        # Verify the custom prompt was passed to create_react_agent
        mock_create_agent.assert_called_once()
        call_kwargs = mock_create_agent.call_args
        assert call_kwargs.kwargs.get("prompt") == custom_prompt


class TestAgentServiceGenerateTitle:
    """Tests for AgentService.generate_title method."""

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_generate_title_short_message(self, mock_create_provider, mock_create_agent):
        """Test title generation for short messages."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        title = service.generate_title("Hello, how are you?")

        assert title == "Hello, how are you?"

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_generate_title_long_message_truncates(self, mock_create_provider, mock_create_agent):
        """Test that long messages are truncated to 50 characters."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        long_message = "This is a very long message that should be truncated to exactly fifty characters"
        title = service.generate_title(long_message)

        assert len(title) == 50
        assert title.endswith("...")

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_generate_title_exactly_50_chars(self, mock_create_provider, mock_create_agent):
        """Test message exactly 50 characters is not truncated."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        message = "A" * 50
        title = service.generate_title(message)

        assert title == message
        assert len(title) == 50

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_generate_title_strips_whitespace(self, mock_create_provider, mock_create_agent):
        """Test that whitespace is stripped from messages."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        title = service.generate_title("  Hello world  ")

        assert title == "Hello world"


class TestAgentServiceGenerateResponse:
    """Tests for AgentService.generate_response method."""

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_generate_response_yields_text_delta_events(self, mock_create_provider, mock_create_agent):
        """Test that generate_response yields TextDeltaEvent for text content."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        # Mock agent with text response using "messages" stream mode format
        mock_agent = MagicMock()
        ai_message_chunk = AIMessageChunk(content="Hello, world!")

        # New format: ("messages", (message_chunk, metadata))
        mock_agent.stream.return_value = iter([("messages", (ai_message_chunk, {}))])
        mock_create_agent.return_value = mock_agent

        service = AgentService()
        messages = [{"role": "user", "content": "Hi"}]

        events = list(service.generate_response(messages))

        text_events = [e for e in events if isinstance(e, TextDeltaEvent)]
        assert len(text_events) == 1
        assert text_events[0].delta == "Hello, world!"

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_generate_response_yields_message_complete_event(self, mock_create_provider, mock_create_agent):
        """Test that generate_response yields MessageCompleteEvent at the end."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        # Mock agent with text response using "messages" stream mode format
        mock_agent = MagicMock()
        ai_message_chunk = AIMessageChunk(content="Response text")

        # New format: ("messages", (message_chunk, metadata))
        mock_agent.stream.return_value = iter([("messages", (ai_message_chunk, {}))])
        mock_create_agent.return_value = mock_agent

        service = AgentService()
        messages = [{"role": "user", "content": "Hi"}]

        events = list(service.generate_response(messages))

        complete_events = [e for e in events if isinstance(e, MessageCompleteEvent)]
        assert len(complete_events) == 1
        assert complete_events[0].content == "Response text"

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_generate_response_yields_tool_call_event(self, mock_create_provider, mock_create_agent):
        """Test that generate_response yields ToolCallEvent for tool calls."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        # Mock agent with tool call using "updates" stream mode format
        mock_agent = MagicMock()
        mock_message = MagicMock()
        mock_message.tool_calls = [{"id": "call_123", "name": "add", "args": {"a": 1, "b": 2}}]
        mock_message.content = ""

        # New format: ("updates", {"agent": {"messages": [...]}})
        mock_agent.stream.return_value = iter([("updates", {"agent": {"messages": [mock_message]}})])
        mock_create_agent.return_value = mock_agent

        service = AgentService()
        messages = [{"role": "user", "content": "What is 1 + 2?"}]

        events = list(service.generate_response(messages))

        tool_call_events = [e for e in events if isinstance(e, ToolCallEvent)]
        assert len(tool_call_events) == 1
        assert tool_call_events[0].tool_call_id == "call_123"
        assert tool_call_events[0].tool_name == "add"
        assert tool_call_events[0].input == {"a": 1, "b": 2}

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_generate_response_yields_tool_result_event(self, mock_create_provider, mock_create_agent):
        """Test that generate_response yields ToolResultEvent for tool results."""
        from langchain_core.messages import ToolMessage

        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        # Mock tool message
        mock_tool_message = MagicMock(spec=ToolMessage)
        mock_tool_message.tool_call_id = "call_123"
        mock_tool_message.content = "3"

        mock_agent = MagicMock()
        # New format: ("updates", {"tools": {"messages": [...]}})
        mock_agent.stream.return_value = iter([("updates", {"tools": {"messages": [mock_tool_message]}})])
        mock_create_agent.return_value = mock_agent

        service = AgentService()
        messages = [{"role": "user", "content": "What is 1 + 2?"}]

        events = list(service.generate_response(messages))

        tool_result_events = [e for e in events if isinstance(e, ToolResultEvent)]
        assert len(tool_result_events) == 1
        assert tool_result_events[0].tool_call_id == "call_123"
        assert tool_result_events[0].output == "3"
        assert tool_result_events[0].error is None


class TestAgentServiceConvertMessages:
    """Tests for AgentService._convert_messages method."""

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_convert_user_message(self, mock_create_provider, mock_create_agent):
        """Test conversion of user message to HumanMessage."""
        from langchain_core.messages import HumanMessage

        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        messages = [{"role": "user", "content": "Hello"}]

        result = service._convert_messages(messages)

        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)
        assert result[0].content == "Hello"

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_convert_assistant_message(self, mock_create_provider, mock_create_agent):
        """Test conversion of assistant message to AIMessage."""
        from langchain_core.messages import AIMessage

        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        messages = [{"role": "assistant", "content": "Hi there!"}]

        result = service._convert_messages(messages)

        assert len(result) == 1
        assert isinstance(result[0], AIMessage)
        assert result[0].content == "Hi there!"

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_convert_mixed_messages(self, mock_create_provider, mock_create_agent):
        """Test conversion of mixed user and assistant messages."""
        from langchain_core.messages import AIMessage, HumanMessage

        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "user", "content": "How are you?"},
        ]

        result = service._convert_messages(messages)

        assert len(result) == 3
        assert isinstance(result[0], HumanMessage)
        assert isinstance(result[1], AIMessage)
        assert isinstance(result[2], HumanMessage)


class TestAgentServiceHelperMethods:
    """Tests for AgentService helper methods."""

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_extract_text_content_from_string(self, mock_create_provider, mock_create_agent):
        """Test _extract_text_content with string input."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        result = service._extract_text_content("Hello, world!")

        assert result == "Hello, world!"

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_extract_text_content_from_list_of_dicts(self, mock_create_provider, mock_create_agent):
        """Test _extract_text_content with list of dicts input."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        content = [
            {"type": "text", "text": "Hello, "},
            {"type": "text", "text": "world!"},
        ]
        result = service._extract_text_content(content)

        assert result == "Hello, world!"

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_extract_text_content_from_list_of_strings(self, mock_create_provider, mock_create_agent):
        """Test _extract_text_content with list of strings input."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        content = ["Hello, ", "world!"]
        result = service._extract_text_content(content)

        assert result == "Hello, world!"

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_extract_text_content_empty(self, mock_create_provider, mock_create_agent):
        """Test _extract_text_content with empty/invalid input."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()

        assert service._extract_text_content(None) == ""
        assert service._extract_text_content(123) == ""
        assert service._extract_text_content([]) == ""

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_handle_messages_stream_with_valid_ai_message(self, mock_create_provider, mock_create_agent):
        """Test _handle_messages_stream with valid AIMessageChunk data."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        ai_chunk = AIMessageChunk(content="Hello!")
        data = (ai_chunk, {})

        result = service._handle_messages_stream(data)

        assert result == "Hello!"

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_handle_messages_stream_with_invalid_data(self, mock_create_provider, mock_create_agent):
        """Test _handle_messages_stream with invalid data."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()

        assert service._handle_messages_stream(None) is None
        assert service._handle_messages_stream(("single",)) is None
        assert service._handle_messages_stream("not a tuple") is None

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_handle_messages_stream_with_empty_content(self, mock_create_provider, mock_create_agent):
        """Test _handle_messages_stream with empty content."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        ai_chunk = AIMessageChunk(content="")
        data = (ai_chunk, {})

        result = service._handle_messages_stream(data)

        assert result is None

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_handle_messages_stream_ignores_tool_messages(self, mock_create_provider, mock_create_agent):
        """Test _handle_messages_stream ignores ToolMessage to prevent tool output leakage."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        # ToolMessage should be ignored even if it has content
        tool_msg = ToolMessage(content="Tool output: 42", tool_call_id="call_123")
        data = (tool_msg, {})

        result = service._handle_messages_stream(data)

        assert result is None

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_handle_messages_stream_ignores_non_ai_messages(self, mock_create_provider, mock_create_agent):
        """Test _handle_messages_stream ignores non-AIMessageChunk types."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        # Generic MagicMock (not AIMessageChunk) should be ignored
        mock_chunk = MagicMock()
        mock_chunk.content = "This should be ignored"
        data = (mock_chunk, {})

        result = service._handle_messages_stream(data)

        assert result is None

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_process_agent_node_with_tool_calls(self, mock_create_provider, mock_create_agent):
        """Test _process_agent_node emits ToolCallEvents."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        mock_message = MagicMock()
        mock_message.tool_calls = [{"id": "call_1", "name": "add", "args": {"a": 1}}]
        node_output = {"messages": [mock_message]}
        emitted = set()

        events = list(service._process_agent_node(node_output, emitted))

        assert len(events) == 1
        assert events[0].tool_call_id == "call_1"
        assert "call_1" in emitted

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_process_agent_node_deduplicates_tool_calls(self, mock_create_provider, mock_create_agent):
        """Test _process_agent_node doesn't emit duplicate tool calls."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        mock_message = MagicMock()
        mock_message.tool_calls = [{"id": "call_1", "name": "add", "args": {}}]
        node_output = {"messages": [mock_message]}
        emitted = {"call_1"}  # Already emitted

        events = list(service._process_agent_node(node_output, emitted))

        assert len(events) == 0

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_process_tools_node(self, mock_create_provider, mock_create_agent):
        """Test _process_tools_node emits ToolResultEvents."""
        from langchain_core.messages import ToolMessage

        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        service = AgentService()
        mock_tool_msg = MagicMock(spec=ToolMessage)
        mock_tool_msg.tool_call_id = "call_1"
        mock_tool_msg.content = "42"
        node_output = {"messages": [mock_tool_msg]}

        events = list(service._process_tools_node(node_output))

        assert len(events) == 1
        assert events[0].tool_call_id == "call_1"
        assert events[0].output == "42"
        assert events[0].error is None


class TestEventDataclasses:
    """Tests for event dataclasses."""

    def test_tool_call_event_creation(self):
        """Test ToolCallEvent dataclass creation."""
        event = ToolCallEvent(
            tool_call_id="call_123",
            tool_name="add",
            input={"a": 1, "b": 2},
        )

        assert event.tool_call_id == "call_123"
        assert event.tool_name == "add"
        assert event.input == {"a": 1, "b": 2}

    def test_tool_result_event_success(self):
        """Test ToolResultEvent for successful execution."""
        event = ToolResultEvent(
            tool_call_id="call_123",
            output="3",
            error=None,
        )

        assert event.tool_call_id == "call_123"
        assert event.output == "3"
        assert event.error is None

    def test_tool_result_event_error(self):
        """Test ToolResultEvent for failed execution."""
        event = ToolResultEvent(
            tool_call_id="call_123",
            output=None,
            error="Division by zero",
        )

        assert event.tool_call_id == "call_123"
        assert event.output is None
        assert event.error == "Division by zero"

    def test_text_delta_event(self):
        """Test TextDeltaEvent dataclass creation."""
        event = TextDeltaEvent(delta="Hello")

        assert event.delta == "Hello"

    def test_message_complete_event(self):
        """Test MessageCompleteEvent dataclass creation."""
        event = MessageCompleteEvent(content="Full response text")

        assert event.content == "Full response text"

    def test_retry_event(self):
        """Test RetryEvent dataclass creation."""
        event = RetryEvent(
            attempt=1,
            max_attempts=3,
            error_type=LLMErrorType.RATE_LIMIT,
            delay=1.0,
        )

        assert event.attempt == 1
        assert event.max_attempts == 3
        assert event.error_type == LLMErrorType.RATE_LIMIT
        assert event.delay == 1.0


class TestAgentServiceRetry:
    """Tests for AgentService retry logic."""

    @patch("app.services.agent_service.time.sleep")
    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_retry_on_rate_limit_error(self, mock_create_provider, mock_create_agent, mock_sleep):
        """Test that RateLimitError triggers retries with exponential backoff."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        # Mock agent that fails on first call, succeeds on second
        mock_agent = MagicMock()
        ai_message_chunk = AIMessageChunk(content="Success!")

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RateLimitError(
                    message="Rate limit exceeded",
                    response=Response(429, request=Request("POST", "https://api.anthropic.com")),
                    body=None,
                )
            return iter([("messages", (ai_message_chunk, {}))])

        mock_agent.stream.side_effect = side_effect
        mock_create_agent.return_value = mock_agent

        service = AgentService()
        messages = [{"role": "user", "content": "Hi"}]

        events = list(service.generate_response(messages))

        # Should have retry event + text delta + message complete
        retry_events = [e for e in events if isinstance(e, RetryEvent)]
        assert len(retry_events) == 1
        assert retry_events[0].error_type == LLMErrorType.RATE_LIMIT
        assert retry_events[0].attempt == 1
        assert mock_sleep.called

    @patch("app.services.agent_service.time.sleep")
    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_retry_on_connection_error(self, mock_create_provider, mock_create_agent, mock_sleep):
        """Test that APIConnectionError triggers retries."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        mock_agent = MagicMock()
        ai_message_chunk = AIMessageChunk(content="Success!")

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise APIConnectionError(request=Request("POST", "https://api.anthropic.com"))
            return iter([("messages", (ai_message_chunk, {}))])

        mock_agent.stream.side_effect = side_effect
        mock_create_agent.return_value = mock_agent

        service = AgentService()
        messages = [{"role": "user", "content": "Hi"}]

        events = list(service.generate_response(messages))

        retry_events = [e for e in events if isinstance(e, RetryEvent)]
        assert len(retry_events) == 1
        assert retry_events[0].error_type == LLMErrorType.CONNECTION

    @patch("app.services.agent_service.time.sleep")
    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_retry_on_server_error(self, mock_create_provider, mock_create_agent, mock_sleep):
        """Test that 500+ errors trigger retries."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        mock_agent = MagicMock()
        ai_message_chunk = AIMessageChunk(content="Success!")

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise APIStatusError(
                    message="Internal Server Error",
                    response=Response(500, request=Request("POST", "https://api.anthropic.com")),
                    body=None,
                )
            return iter([("messages", (ai_message_chunk, {}))])

        mock_agent.stream.side_effect = side_effect
        mock_create_agent.return_value = mock_agent

        service = AgentService()
        messages = [{"role": "user", "content": "Hi"}]

        events = list(service.generate_response(messages))

        retry_events = [e for e in events if isinstance(e, RetryEvent)]
        assert len(retry_events) == 1
        assert retry_events[0].error_type == LLMErrorType.SERVER_ERROR

    @patch("app.services.agent_service.time.sleep")
    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_max_retries_exhausted_raises_rate_limit_error(self, mock_create_provider, mock_create_agent, mock_sleep):
        """Test that exhausting max_retries raises LLMRateLimitError."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 2
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        mock_agent = MagicMock()
        mock_agent.stream.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=Response(429, request=Request("POST", "https://api.anthropic.com")),
            body=None,
        )
        mock_create_agent.return_value = mock_agent

        service = AgentService()
        messages = [{"role": "user", "content": "Hi"}]

        with pytest.raises(LLMRateLimitError):
            list(service.generate_response(messages))

    @patch("app.services.agent_service.time.sleep")
    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_max_retries_exhausted_raises_connection_error(self, mock_create_provider, mock_create_agent, mock_sleep):
        """Test that exhausting max_retries on connection error raises LLMConnectionError."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 2
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        mock_agent = MagicMock()
        mock_agent.stream.side_effect = APIConnectionError(request=Request("POST", "https://api.anthropic.com"))
        mock_create_agent.return_value = mock_agent

        service = AgentService()
        messages = [{"role": "user", "content": "Hi"}]

        with pytest.raises(LLMConnectionError):
            list(service.generate_response(messages))

    @patch("app.services.agent_service.time.sleep")
    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_exponential_backoff_delay(self, mock_create_provider, mock_create_agent, mock_sleep):
        """Test exponential backoff delay calculation."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 4
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        mock_agent = MagicMock()
        ai_message_chunk = AIMessageChunk(content="Success!")

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 3:
                raise APIConnectionError(request=Request("POST", "https://api.anthropic.com"))
            return iter([("messages", (ai_message_chunk, {}))])

        mock_agent.stream.side_effect = side_effect
        mock_create_agent.return_value = mock_agent

        service = AgentService()
        messages = [{"role": "user", "content": "Hi"}]

        events = list(service.generate_response(messages))

        retry_events = [e for e in events if isinstance(e, RetryEvent)]
        assert len(retry_events) == 3
        # Verify exponential backoff: 1.0, 2.0, 4.0
        assert retry_events[0].delay == 1.0
        assert retry_events[1].delay == 2.0
        assert retry_events[2].delay == 4.0

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_context_length_error_no_retry(self, mock_create_provider, mock_create_agent):
        """Test that context length error does not trigger retries."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        mock_agent = MagicMock()
        mock_agent.stream.side_effect = APIStatusError(
            message="context_length exceeded",
            response=Response(400, request=Request("POST", "https://api.anthropic.com")),
            body=None,
        )
        mock_create_agent.return_value = mock_agent

        service = AgentService()
        messages = [{"role": "user", "content": "Hi"}]

        with pytest.raises(LLMContextLengthError):
            list(service.generate_response(messages))

        # Should not retry - only one call
        assert mock_agent.stream.call_count == 1

    @patch("app.services.agent_service.time.sleep")
    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_client_error_no_retry(self, mock_create_provider, mock_create_agent, mock_sleep):
        """Test that 4xx errors (except context length) do not trigger retries."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096
        mock_provider.config.max_retries = 3
        mock_provider.config.retry_delay = 1.0
        mock_create_provider.return_value = mock_provider

        mock_agent = MagicMock()
        mock_agent.stream.side_effect = APIStatusError(
            message="Bad request",
            response=Response(400, request=Request("POST", "https://api.anthropic.com")),
            body=None,
        )
        mock_create_agent.return_value = mock_agent

        service = AgentService()
        messages = [{"role": "user", "content": "Hi"}]

        with pytest.raises(LLMStreamError):
            list(service.generate_response(messages))

        # Should not retry - only one call
        assert mock_agent.stream.call_count == 1
        assert not mock_sleep.called
