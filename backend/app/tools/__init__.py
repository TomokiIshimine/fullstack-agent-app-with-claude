"""Tool registry for managing available agent tools."""

from __future__ import annotations

import logging
from typing import Any, Callable, Sequence

from langchain_core.tools import BaseTool as LangChainBaseTool

from .calculator import CALCULATOR_TOOLS

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing available tools for the agent.

    Provides a central location to register and retrieve tools
    for use with the LangGraph ReAct agent.

    Usage:
        registry = ToolRegistry()
        registry.register_defaults()  # Register calculator tools
        tools = registry.get_all_tools()
    """

    def __init__(self) -> None:
        """Initialize empty tool registry."""
        self._tools: dict[str, LangChainBaseTool | Callable[..., Any]] = {}

    def register(self, tool: LangChainBaseTool | Callable[..., Any]) -> None:
        """Register a single tool.

        Args:
            tool: LangChain tool or callable decorated with @tool
        """
        # LangChain StructuredTool has 'name' attribute, regular functions have '__name__'
        raw_name = getattr(tool, "name", None) or getattr(tool, "__name__", None) or str(tool)
        name = str(raw_name)
        self._tools[name] = tool
        logger.debug(f"Registered tool: {name}")

    def register_many(self, tools: Sequence[LangChainBaseTool | Callable[..., Any]]) -> None:
        """Register multiple tools at once."""
        for tool in tools:
            self.register(tool)

    def register_defaults(self) -> None:
        """Register all default tools (calculator)."""
        self.register_many(CALCULATOR_TOOLS)
        logger.info(f"Registered {len(CALCULATOR_TOOLS)} default tools")

    def get_all_tools(self) -> list[LangChainBaseTool | Callable[..., Any]]:
        """Get all registered tools as a list."""
        return list(self._tools.values())

    def get_tool(self, name: str) -> LangChainBaseTool | Callable[..., Any] | None:
        """Get a specific tool by name."""
        return self._tools.get(name)

    def list_tool_names(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())


# Global registry instance
_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _registry.register_defaults()
    return _registry


__all__ = ["ToolRegistry", "get_tool_registry", "CALCULATOR_TOOLS"]
