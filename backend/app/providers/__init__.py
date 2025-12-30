"""LLM Provider abstraction layer.

This module provides a unified interface for different LLM providers,
enabling easy switching between providers (Anthropic, OpenAI, etc.)
through dependency injection.

Example usage:
    # Using factory function
    from app.providers import create_provider, load_llm_config

    config = load_llm_config()
    provider = create_provider(config)
    chat_model = provider.create_chat_model()

    # Direct provider instantiation
    from app.providers import AnthropicProvider, AnthropicConfig

    config = AnthropicConfig.from_env()
    provider = AnthropicProvider(config)
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from app.constants.agent import DEFAULT_LLM_MODEL, DEFAULT_LLM_PROVIDER, DEFAULT_MAX_TOKENS
from app.core.exceptions import ProviderConfigurationError, ProviderNotFoundError
from app.providers.anthropic import AnthropicConfig, AnthropicProvider
from app.providers.base import BaseLLMProvider, LLMConfig

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Registry of supported providers
_PROVIDER_REGISTRY: dict[str, type[BaseLLMProvider]] = {
    "anthropic": AnthropicProvider,
}


def register_provider(name: str, provider_class: type[BaseLLMProvider]) -> None:
    """Register a new LLM provider.

    Args:
        name: Provider name (e.g., "openai", "anthropic").
        provider_class: Provider class that extends BaseLLMProvider.

    Raises:
        ProviderConfigurationError: If provider name is already registered.
    """
    if name in _PROVIDER_REGISTRY:
        raise ProviderConfigurationError(f"プロバイダー '{name}' は既に登録されています", field="name")
    _PROVIDER_REGISTRY[name] = provider_class
    logger.info(f"Registered LLM provider: {name}")


def get_supported_providers() -> list[str]:
    """Return list of supported provider names."""
    return list(_PROVIDER_REGISTRY.keys())


def load_llm_config() -> LLMConfig:
    """Load LLM configuration from environment variables.

    Returns:
        LLMConfig populated from environment variables.
    """
    provider = os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER)

    # Use provider-specific config factory if available
    if provider == "anthropic":
        return AnthropicConfig.from_env()

    # Fallback for other providers
    model = os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL)
    max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))

    return LLMConfig(
        provider=provider,
        model=model,
        max_tokens=max_tokens,
        streaming=True,
    )


def create_provider(config: LLMConfig | None = None) -> BaseLLMProvider:
    """Create an LLM provider instance based on configuration.

    Factory function that creates the appropriate provider based on
    the configuration's provider field.

    Args:
        config: LLM configuration. If None, loads from environment.

    Returns:
        Configured BaseLLMProvider instance.

    Raises:
        ProviderNotFoundError: If the specified provider is not supported.

    Example:
        # Using default configuration from environment
        provider = create_provider()

        # Using explicit configuration
        config = LLMConfig(provider="anthropic", model="claude-sonnet-4-5-20250929")
        provider = create_provider(config)
    """
    if config is None:
        config = load_llm_config()

    provider_name = config.provider.lower()

    if provider_name not in _PROVIDER_REGISTRY:
        raise ProviderNotFoundError(provider_name, get_supported_providers())

    provider_class = _PROVIDER_REGISTRY[provider_name]
    provider = provider_class(config)

    logger.info(f"Created LLM provider: {provider}")
    return provider


__all__ = [
    # Base classes
    "BaseLLMProvider",
    "LLMConfig",
    # Anthropic
    "AnthropicProvider",
    "AnthropicConfig",
    # Factory functions
    "create_provider",
    "load_llm_config",
    "register_provider",
    "get_supported_providers",
]
