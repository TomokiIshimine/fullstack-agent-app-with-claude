"""Tests for AgentService (LangGraph ReAct agent integration)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.agent_service import (
    AgentConfig,
    AgentService,
    MessageCompleteEvent,
    SYSTEM_PROMPT,
    TextDeltaEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from app.tools import ToolRegistry


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = AgentConfig()

        assert config.provider == "anthropic"
        assert config.model_name == "claude-sonnet-4-5-20250929"
        assert config.max_tokens == 4096
        assert config.system_prompt == SYSTEM_PROMPT

    def test_custom_values(self):
        """Test custom configuration values."""
        config = AgentConfig(
            provider="custom",
            model_name="custom-model",
            max_tokens=8192,
            system_prompt="Custom prompt",
        )

        assert config.provider == "custom"
        assert config.model_name == "custom-model"
        assert config.max_tokens == 8192
        assert config.system_prompt == "Custom prompt"

    def test_from_env_with_defaults(self, monkeypatch):
        """Test from_env uses default values when env vars not set."""
        # Clear any existing env vars
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.delenv("LLM_MODEL", raising=False)
        monkeypatch.delenv("CLAUDE_MAX_TOKENS", raising=False)

        config = AgentConfig.from_env()

        assert config.provider == "anthropic"
        assert config.model_name == "claude-sonnet-4-5-20250929"
        assert config.max_tokens == 4096

    def test_from_env_with_custom_values(self, monkeypatch):
        """Test from_env reads custom values from environment."""
        monkeypatch.setenv("LLM_PROVIDER", "custom_provider")
        monkeypatch.setenv("LLM_MODEL", "custom-model-v2")
        monkeypatch.setenv("CLAUDE_MAX_TOKENS", "2048")

        config = AgentConfig.from_env()

        assert config.provider == "custom_provider"
        assert config.model_name == "custom-model-v2"
        assert config.max_tokens == 2048


class TestAgentServiceInit:
    """Tests for AgentService initialization."""

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatAnthropic")
    def test_init_with_default_config(self, mock_chat_anthropic, mock_create_agent):
        """Test initialization with default configuration."""
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

        service = AgentService()

        assert service.config.provider == "anthropic"
        mock_chat_anthropic.assert_called_once()
        mock_create_agent.assert_called_once()

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatAnthropic")
    def test_init_with_custom_config(self, mock_chat_anthropic, mock_create_agent):
        """Test initialization with custom configuration."""
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

        config = AgentConfig(
            provider="anthropic",
            model_name="claude-opus-4",
            max_tokens=8192,
        )
        service = AgentService(config=config)

        assert service.config.model_name == "claude-opus-4"
        assert service.config.max_tokens == 8192

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatAnthropic")
    def test_init_with_custom_tool_registry(self, mock_chat_anthropic, mock_create_agent):
        """Test initialization with custom tool registry."""
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

        registry = ToolRegistry()
        service = AgentService(tool_registry=registry)

        assert service.tools == []

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatAnthropic")
    def test_init_registers_default_tools(self, mock_chat_anthropic, mock_create_agent):
        """Test that initialization registers default tools from global registry."""
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

        service = AgentService()

        # Default registry should have calculator tools
        assert len(service.tools) > 0

    def test_init_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises ValueError."""
        config = AgentConfig(provider="unsupported_provider")

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            AgentService(config=config)


class TestAgentServiceGenerateTitle:
    """Tests for AgentService.generate_title method."""

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatAnthropic")
    def test_generate_title_short_message(self, mock_chat_anthropic, mock_create_agent):
        """Test title generation for short messages."""
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

        service = AgentService()
        title = service.generate_title("Hello, how are you?")

        assert title == "Hello, how are you?"

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatAnthropic")
    def test_generate_title_long_message_truncates(self, mock_chat_anthropic, mock_create_agent):
        """Test that long messages are truncated to 50 characters."""
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

        service = AgentService()
        long_message = "This is a very long message that should be truncated to exactly fifty characters"
        title = service.generate_title(long_message)

        assert len(title) == 50
        assert title.endswith("...")

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatAnthropic")
    def test_generate_title_exactly_50_chars(self, mock_chat_anthropic, mock_create_agent):
        """Test message exactly 50 characters is not truncated."""
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

        service = AgentService()
        message = "A" * 50
        title = service.generate_title(message)

        assert title == message
        assert len(title) == 50

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatAnthropic")
    def test_generate_title_strips_whitespace(self, mock_chat_anthropic, mock_create_agent):
        """Test that whitespace is stripped from messages."""
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

        service = AgentService()
        title = service.generate_title("  Hello world  ")

        assert title == "Hello world"


class TestAgentServiceGenerateResponse:
    """Tests for AgentService.generate_response method."""

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatAnthropic")
    def test_generate_response_yields_text_delta_events(self, mock_chat_anthropic, mock_create_agent):
        """Test that generate_response yields TextDeltaEvent for text content."""
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

        # Mock agent with text response
        mock_agent = MagicMock()
        mock_message = MagicMock()
        mock_message.tool_calls = None
        mock_message.content = "Hello, world!"

        mock_agent.stream.return_value = iter([
            {"agent": {"messages": [mock_message]}}
        ])
        mock_create_agent.return_value = mock_agent

        service = AgentService()
        messages = [{"role": "user", "content": "Hi"}]

        events = list(service.generate_response(messages))

        text_events = [e for e in events if isinstance(e, TextDeltaEvent)]
        assert len(text_events) == 1
        assert text_events[0].delta == "Hello, world!"

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatAnthropic")
    def test_generate_response_yields_message_complete_event(self, mock_chat_anthropic, mock_create_agent):
        """Test that generate_response yields MessageCompleteEvent at the end."""
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

        # Mock agent with text response
        mock_agent = MagicMock()
        mock_message = MagicMock()
        mock_message.tool_calls = None
        mock_message.content = "Response text"

        mock_agent.stream.return_value = iter([
            {"agent": {"messages": [mock_message]}}
        ])
        mock_create_agent.return_value = mock_agent

        service = AgentService()
        messages = [{"role": "user", "content": "Hi"}]

        events = list(service.generate_response(messages))

        complete_events = [e for e in events if isinstance(e, MessageCompleteEvent)]
        assert len(complete_events) == 1
        assert complete_events[0].content == "Response text"

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatAnthropic")
    def test_generate_response_yields_tool_call_event(self, mock_chat_anthropic, mock_create_agent):
        """Test that generate_response yields ToolCallEvent for tool calls."""
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

        # Mock agent with tool call
        mock_agent = MagicMock()
        mock_message = MagicMock()
        mock_message.tool_calls = [
            {"id": "call_123", "name": "add", "args": {"a": 1, "b": 2}}
        ]
        mock_message.content = ""

        mock_agent.stream.return_value = iter([
            {"agent": {"messages": [mock_message]}}
        ])
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
    @patch("app.services.agent_service.ChatAnthropic")
    def test_generate_response_yields_tool_result_event(self, mock_chat_anthropic, mock_create_agent):
        """Test that generate_response yields ToolResultEvent for tool results."""
        from langchain_core.messages import ToolMessage

        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

        # Mock tool message
        mock_tool_message = MagicMock(spec=ToolMessage)
        mock_tool_message.tool_call_id = "call_123"
        mock_tool_message.content = "3"

        mock_agent = MagicMock()
        mock_agent.stream.return_value = iter([
            {"tools": {"messages": [mock_tool_message]}}
        ])
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
    @patch("app.services.agent_service.ChatAnthropic")
    def test_convert_user_message(self, mock_chat_anthropic, mock_create_agent):
        """Test conversion of user message to HumanMessage."""
        from langchain_core.messages import HumanMessage

        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

        service = AgentService()
        messages = [{"role": "user", "content": "Hello"}]

        result = service._convert_messages(messages)

        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)
        assert result[0].content == "Hello"

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatAnthropic")
    def test_convert_assistant_message(self, mock_chat_anthropic, mock_create_agent):
        """Test conversion of assistant message to AIMessage."""
        from langchain_core.messages import AIMessage

        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

        service = AgentService()
        messages = [{"role": "assistant", "content": "Hi there!"}]

        result = service._convert_messages(messages)

        assert len(result) == 1
        assert isinstance(result[0], AIMessage)
        assert result[0].content == "Hi there!"

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatAnthropic")
    def test_convert_mixed_messages(self, mock_chat_anthropic, mock_create_agent):
        """Test conversion of mixed user and assistant messages."""
        from langchain_core.messages import AIMessage, HumanMessage

        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm

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
