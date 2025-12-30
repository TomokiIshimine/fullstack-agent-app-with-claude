"""Tests for LLM provider abstraction layer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import ProviderAPIKeyError, ProviderConfigurationError, ProviderNotFoundError
from app.providers import (
    AnthropicConfig,
    AnthropicProvider,
    BaseLLMProvider,
    LLMConfig,
    create_provider,
    get_supported_providers,
    load_llm_config,
    register_provider,
)


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""

    def test_default_values(self):
        """Test LLMConfig with default values."""
        config = LLMConfig(provider="test", model="test-model")

        assert config.provider == "test"
        assert config.model == "test-model"
        assert config.max_tokens == 4096
        assert config.streaming is True

    def test_custom_values(self):
        """Test LLMConfig with custom values."""
        config = LLMConfig(
            provider="custom",
            model="custom-model",
            max_tokens=8192,
            streaming=False,
        )

        assert config.provider == "custom"
        assert config.model == "custom-model"
        assert config.max_tokens == 8192
        assert config.streaming is False

    def test_empty_provider_raises_error(self):
        """Test that empty provider raises ProviderConfigurationError."""
        with pytest.raises(ProviderConfigurationError, match="プロバイダー名は必須です"):
            LLMConfig(provider="", model="model")

    def test_empty_model_raises_error(self):
        """Test that empty model raises ProviderConfigurationError."""
        with pytest.raises(ProviderConfigurationError, match="モデル名は必須です"):
            LLMConfig(provider="test", model="")

    def test_invalid_max_tokens_raises_error(self):
        """Test that non-positive max_tokens raises ProviderConfigurationError."""
        with pytest.raises(ProviderConfigurationError, match="max_tokensは正の整数"):
            LLMConfig(provider="test", model="model", max_tokens=0)

        with pytest.raises(ProviderConfigurationError, match="max_tokensは正の整数"):
            LLMConfig(provider="test", model="model", max_tokens=-1)

    def test_default_retry_values(self):
        """Test LLMConfig with default retry values."""
        config = LLMConfig(provider="test", model="test-model")

        assert config.max_retries == 3
        assert config.retry_delay == 1.0

    def test_custom_retry_values(self):
        """Test LLMConfig with custom retry values."""
        config = LLMConfig(
            provider="test",
            model="test-model",
            max_retries=5,
            retry_delay=2.0,
        )

        assert config.max_retries == 5
        assert config.retry_delay == 2.0

    def test_invalid_max_retries_raises_error(self):
        """Test that negative max_retries raises ProviderConfigurationError."""
        with pytest.raises(ProviderConfigurationError, match="max_retriesは0以上"):
            LLMConfig(provider="test", model="model", max_retries=-1)

    def test_invalid_retry_delay_raises_error(self):
        """Test that negative retry_delay raises ProviderConfigurationError."""
        with pytest.raises(ProviderConfigurationError, match="retry_delayは0以上"):
            LLMConfig(provider="test", model="model", retry_delay=-0.5)

    def test_zero_max_retries_allowed(self):
        """Test that zero max_retries is allowed (no retries)."""
        config = LLMConfig(provider="test", model="model", max_retries=0)

        assert config.max_retries == 0

    def test_zero_retry_delay_allowed(self):
        """Test that zero retry_delay is allowed (no delay between retries)."""
        config = LLMConfig(provider="test", model="model", retry_delay=0.0)

        assert config.retry_delay == 0.0


class TestAnthropicConfig:
    """Tests for AnthropicConfig dataclass."""

    def test_default_values(self):
        """Test AnthropicConfig with default values."""
        config = AnthropicConfig(provider="anthropic", model="claude-3")

        assert config.provider == "anthropic"
        assert config.model == "claude-3"
        assert config.api_key is None or config.api_key  # May be set from env

    def test_from_env_defaults(self, monkeypatch):
        """Test from_env with default environment."""
        monkeypatch.delenv("LLM_MODEL", raising=False)
        monkeypatch.delenv("CLAUDE_MAX_TOKENS", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        config = AnthropicConfig.from_env()

        assert config.provider == "anthropic"
        assert config.model == "claude-sonnet-4-5-20250929"
        assert config.max_tokens == 4096
        assert config.streaming is True

    def test_from_env_custom_values(self, monkeypatch):
        """Test from_env with custom environment values."""
        monkeypatch.setenv("LLM_MODEL", "claude-opus-4")
        monkeypatch.setenv("CLAUDE_MAX_TOKENS", "8192")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        config = AnthropicConfig.from_env()

        assert config.model == "claude-opus-4"
        assert config.max_tokens == 8192
        assert config.api_key == "test-key"

    def test_from_env_with_overrides(self, monkeypatch):
        """Test from_env with parameter overrides."""
        monkeypatch.setenv("LLM_MODEL", "claude-3")
        monkeypatch.setenv("CLAUDE_MAX_TOKENS", "4096")

        config = AnthropicConfig.from_env(model="override-model", max_tokens=2048)

        assert config.model == "override-model"
        assert config.max_tokens == 2048


class TestAnthropicProvider:
    """Tests for AnthropicProvider."""

    def test_init_with_anthropic_config(self):
        """Test initialization with AnthropicConfig."""
        config = AnthropicConfig(
            provider="anthropic",
            model="claude-3",
            api_key="test-key",
        )
        provider = AnthropicProvider(config)

        assert provider.provider_name == "anthropic"
        assert provider.model_name == "claude-3"

    def test_init_with_base_config(self):
        """Test initialization with base LLMConfig converts to AnthropicConfig."""
        config = LLMConfig(provider="anthropic", model="claude-3")
        provider = AnthropicProvider(config)

        assert provider.provider_name == "anthropic"
        assert provider.model_name == "claude-3"

    @patch("app.providers.anthropic.ChatAnthropic")
    def test_create_chat_model_success(self, mock_chat_anthropic):
        """Test successful chat model creation."""
        mock_chat_anthropic.return_value = MagicMock()

        config = AnthropicConfig(
            provider="anthropic",
            model="claude-3",
            max_tokens=4096,
            api_key="test-key",
        )
        provider = AnthropicProvider(config)
        model = provider.create_chat_model()

        assert model is not None
        mock_chat_anthropic.assert_called_once()

    def test_create_chat_model_missing_api_key(self, monkeypatch):
        """Test that missing API key raises ProviderAPIKeyError."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        config = AnthropicConfig(
            provider="anthropic",
            model="claude-3",
            api_key=None,
        )
        provider = AnthropicProvider(config)

        with pytest.raises(ProviderAPIKeyError, match="AIサービスの設定に問題があります"):
            provider.create_chat_model()

    def test_repr(self):
        """Test string representation."""
        config = AnthropicConfig(
            provider="anthropic",
            model="claude-3",
            api_key="test-key",
        )
        provider = AnthropicProvider(config)

        repr_str = repr(provider)
        assert "AnthropicProvider" in repr_str
        assert "anthropic" in repr_str
        assert "claude-3" in repr_str


class TestProviderFactory:
    """Tests for provider factory functions."""

    def test_get_supported_providers(self):
        """Test getting list of supported providers."""
        providers = get_supported_providers()

        assert "anthropic" in providers

    def test_load_llm_config_defaults(self, monkeypatch):
        """Test load_llm_config with default environment."""
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.delenv("LLM_MODEL", raising=False)
        monkeypatch.delenv("CLAUDE_MAX_TOKENS", raising=False)

        config = load_llm_config()

        assert config.provider == "anthropic"
        assert config.model == "claude-sonnet-4-5-20250929"
        assert config.max_tokens == 4096

    def test_load_llm_config_custom(self, monkeypatch):
        """Test load_llm_config with custom environment."""
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("LLM_MODEL", "claude-opus-4")
        monkeypatch.setenv("CLAUDE_MAX_TOKENS", "8192")

        config = load_llm_config()

        assert config.provider == "anthropic"
        assert config.model == "claude-opus-4"
        assert config.max_tokens == 8192

    @patch("app.providers.anthropic.ChatAnthropic")
    def test_create_provider_anthropic(self, mock_chat_anthropic, monkeypatch):
        """Test creating Anthropic provider via factory."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        config = LLMConfig(provider="anthropic", model="claude-3")
        provider = create_provider(config)

        assert isinstance(provider, AnthropicProvider)
        assert provider.provider_name == "anthropic"

    def test_create_provider_unsupported(self):
        """Test that unsupported provider raises ProviderNotFoundError."""
        config = LLMConfig(provider="unsupported", model="model")

        with pytest.raises(ProviderNotFoundError, match="サポートされていないLLMプロバイダー"):
            create_provider(config)

    @patch("app.providers.anthropic.ChatAnthropic")
    def test_create_provider_default_config(self, mock_chat_anthropic, monkeypatch):
        """Test creating provider with default config from environment."""
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        provider = create_provider()

        assert isinstance(provider, AnthropicProvider)


class TestRegisterProvider:
    """Tests for dynamic provider registration."""

    def test_register_new_provider(self):
        """Test registering a new provider."""

        class MockProvider(BaseLLMProvider):
            def create_chat_model(self):
                return MagicMock()

        # Register should not raise
        register_provider("mock_test", MockProvider)

        assert "mock_test" in get_supported_providers()

    def test_register_duplicate_provider_raises_error(self):
        """Test that registering duplicate provider raises ProviderConfigurationError."""

        class MockProvider(BaseLLMProvider):
            def create_chat_model(self):
                return MagicMock()

        # First registration should succeed
        register_provider("mock_duplicate", MockProvider)

        # Second registration should fail
        with pytest.raises(ProviderConfigurationError, match="既に登録されています"):
            register_provider("mock_duplicate", MockProvider)
