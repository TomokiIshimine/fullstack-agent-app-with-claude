"""Base classes for tool implementation."""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for custom tools (future use).

    This class provides a template for implementing custom tools
    that may require more complex initialization or state management
    than what the @tool decorator provides.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for registration."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM."""
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> str:
        """Execute the tool with given arguments."""
        pass


__all__ = ["BaseTool"]
