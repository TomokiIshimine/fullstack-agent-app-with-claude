"""Base LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.exceptions import ProviderConfigurationError

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


@dataclass
class LLMConfig:
    """Configuration for LLM providers.

    This configuration is provider-agnostic and contains common settings
    that apply to all LLM providers.
    """

    provider: str
    model: str
    max_tokens: int = 4096
    streaming: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.provider:
            raise ProviderConfigurationError("プロバイダー名は必須です", field="provider")
        if not self.model:
            raise ProviderConfigurationError("モデル名は必須です", field="model")
        if self.max_tokens <= 0:
            raise ProviderConfigurationError("max_tokensは正の整数である必要があります", field="max_tokens")


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.

    This class defines the interface that all LLM providers must implement.
    It enables dependency injection and makes it easy to switch between
    different LLM providers (Anthropic, OpenAI, etc.).

    Example usage:
        config = LLMConfig(provider="anthropic", model="claude-sonnet-4-5-20250929")
        provider = AnthropicProvider(config)
        chat_model = provider.create_chat_model()
    """

    def __init__(self, config: LLMConfig) -> None:
        """Initialize the provider with configuration.

        Args:
            config: LLM configuration containing provider settings.
        """
        self.config = config

    @abstractmethod
    def create_chat_model(self) -> "BaseChatModel":
        """Create and return a LangChain-compatible chat model.

        Returns:
            A BaseChatModel instance configured for this provider.

        Raises:
            ValueError: If configuration is invalid.
            RuntimeError: If the provider cannot be initialized.
        """
        pass

    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return self.config.provider

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return self.config.model

    def __repr__(self) -> str:
        """Return string representation of the provider."""
        return f"{self.__class__.__name__}(provider={self.provider_name!r}, model={self.model_name!r})"


__all__ = ["BaseLLMProvider", "LLMConfig"]
