"""Tests for AgentService (LangGraph ReAct agent integration)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessageChunk, ToolMessage

from app.services.agent_service import SYSTEM_PROMPT, AgentConfig, AgentService, MessageCompleteEvent, TextDeltaEvent, ToolCallEvent, ToolResultEvent
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
    @patch("app.services.agent_service.create_provider")
    def test_init_with_default_config(self, mock_create_provider, mock_create_agent):
        """Test initialization with default configuration."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-sonnet-4-5-20250929"
        mock_provider.config.max_tokens = 4096
        mock_create_provider.return_value = mock_provider

        service = AgentService()

        assert service.config.provider == "anthropic"
        mock_create_provider.assert_called_once()
        mock_create_agent.assert_called_once()

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_init_with_custom_config(self, mock_create_provider, mock_create_agent):
        """Test initialization with custom configuration (backward compatibility)."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_create_provider.return_value = mock_provider

        config = AgentConfig(
            provider="anthropic",
            model_name="claude-opus-4",
            max_tokens=8192,
        )
        service = AgentService(config=config)

        assert service.config.model_name == "claude-opus-4"
        assert service.config.max_tokens == 8192

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_init_with_config_honors_system_prompt(self, mock_create_provider, mock_create_agent):
        """Test that config.system_prompt is honored when using AgentConfig."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_create_provider.return_value = mock_provider

        custom_prompt = "You are a specialized assistant from config."
        config = AgentConfig(
            provider="anthropic",
            model_name="claude-opus-4",
            system_prompt=custom_prompt,
        )
        service = AgentService(config=config)

        assert service._system_prompt == custom_prompt
        # Verify the custom prompt was passed to create_react_agent
        mock_create_agent.assert_called_once()
        call_kwargs = mock_create_agent.call_args
        assert call_kwargs.kwargs.get("prompt") == custom_prompt

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_init_system_prompt_arg_overrides_config(self, mock_create_provider, mock_create_agent):
        """Test that system_prompt argument takes precedence over config.system_prompt."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_create_provider.return_value = mock_provider

        config_prompt = "Prompt from config."
        override_prompt = "Override prompt from argument."
        config = AgentConfig(
            provider="anthropic",
            model_name="claude-opus-4",
            system_prompt=config_prompt,
        )
        service = AgentService(config=config, system_prompt=override_prompt)

        assert service._system_prompt == override_prompt
        # Verify the override prompt was passed to create_react_agent
        mock_create_agent.assert_called_once()
        call_kwargs = mock_create_agent.call_args
        assert call_kwargs.kwargs.get("prompt") == override_prompt

    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.create_provider")
    def test_init_with_provider(self, mock_create_provider, mock_create_agent):
        """Test initialization with LLM provider instance."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-opus-4"
        mock_provider.config.max_tokens = 8192

        service = AgentService(provider=mock_provider)

        assert service.config.provider == "anthropic"
        assert service.config.model_name == "claude-opus-4"
        assert service.provider is mock_provider
        # create_provider should not be called when provider is passed
        mock_create_provider.assert_not_called()

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
        mock_create_provider.return_value = mock_provider

        service = AgentService()

        # Default registry should have calculator tools
        assert len(service.tools) > 0

    def test_init_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises ValueError."""
        config = AgentConfig(provider="unsupported_provider")

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            AgentService(config=config)

    @patch("app.services.agent_service.create_react_agent")
    def test_init_with_custom_system_prompt(self, mock_create_agent):
        """Test initialization with custom system prompt."""
        mock_llm = MagicMock()
        mock_provider = MagicMock()
        mock_provider.create_chat_model.return_value = mock_llm
        mock_provider.provider_name = "anthropic"
        mock_provider.model_name = "claude-3"
        mock_provider.config.max_tokens = 4096

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
