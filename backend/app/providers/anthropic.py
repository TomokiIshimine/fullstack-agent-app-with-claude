"""Anthropic LLM provider implementation."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from langchain_anthropic import ChatAnthropic

from app.core.exceptions import ProviderAPIKeyError
from app.providers.base import BaseLLMProvider, LLMConfig

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


@dataclass
class AnthropicConfig(LLMConfig):
    """Anthropic-specific configuration.

    Extends the base LLMConfig with Anthropic-specific settings.
    """

    api_key: str | None = None

    def __post_init__(self) -> None:
        """Validate and set default values."""
        # Set default provider if not specified
        if not self.provider:
            self.provider = "anthropic"

        # Call parent validation
        super().__post_init__()

        # Resolve API key from environment if not provided
        if not self.api_key:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")

    @classmethod
    def from_env(
        cls,
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> "AnthropicConfig":
        """Create configuration from environment variables.

        Args:
            model: Optional model name override. Defaults to LLM_MODEL env var.
            max_tokens: Optional max tokens override. Defaults to CLAUDE_MAX_TOKENS env var.

        Returns:
            AnthropicConfig instance populated from environment.
        """
        from app.constants.agent import DEFAULT_LLM_MODEL, DEFAULT_MAX_TOKENS

        resolved_model = model if model is not None else os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL)
        resolved_max_tokens = max_tokens if max_tokens is not None else int(os.getenv("CLAUDE_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))

        return cls(
            provider="anthropic",
            model=resolved_model,
            max_tokens=resolved_max_tokens,
            streaming=True,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )


class AnthropicProvider(BaseLLMProvider):
    """LLM provider implementation for Anthropic Claude models.

    This provider creates LangChain-compatible ChatAnthropic instances
    for use with Claude models.

    Example:
        config = AnthropicConfig.from_env()
        provider = AnthropicProvider(config)
        chat_model = provider.create_chat_model()
    """

    def __init__(self, config: AnthropicConfig | LLMConfig) -> None:
        """Initialize Anthropic provider.

        Args:
            config: Configuration for the provider. Can be either AnthropicConfig
                   or base LLMConfig (which will be converted).
        """
        # Convert base LLMConfig to AnthropicConfig if needed
        if not isinstance(config, AnthropicConfig):
            config = AnthropicConfig(
                provider=config.provider,
                model=config.model,
                max_tokens=config.max_tokens,
                streaming=config.streaming,
            )
        super().__init__(config)
        self._anthropic_config: AnthropicConfig = config

    def create_chat_model(self) -> "BaseChatModel":
        """Create a ChatAnthropic instance.

        Returns:
            Configured ChatAnthropic model.

        Raises:
            ProviderAPIKeyError: If API key is not configured.
        """
        if not self._anthropic_config.api_key:
            raise ProviderAPIKeyError("Anthropic")

        logger.debug(
            f"Creating ChatAnthropic model: {self.model_name}, "
            f"max_tokens={self.config.max_tokens}, "
            f"max_retries={self.config.max_retries}, "
            f"streaming={self.config.streaming}"
        )

        return ChatAnthropic(
            model_name=self.model_name,  # type: ignore[call-arg]
            max_tokens_to_sample=self.config.max_tokens,  # type: ignore[call-arg]
            streaming=self.config.streaming,
            api_key=self._anthropic_config.api_key,  # type: ignore[call-arg, arg-type]
            max_retries=self.config.max_retries,  # type: ignore[call-arg]
        )


__all__ = ["AnthropicConfig", "AnthropicProvider"]
