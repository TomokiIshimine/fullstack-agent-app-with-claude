"""Tests for ToolRegistry."""

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_core.tools import tool

from app.tools import CALCULATOR_TOOLS, ToolRegistry, get_tool_registry
from app.tools.calculator import add, divide, multiply, subtract


class TestToolRegistryInit:
    """Tests for ToolRegistry initialization."""

    def test_init_creates_empty_registry(self):
        """Test that initialization creates an empty registry."""
        registry = ToolRegistry()

        assert len(registry.get_all_tools()) == 0

    def test_init_tools_dict_is_empty(self):
        """Test that internal tools dict is empty on init."""
        registry = ToolRegistry()

        assert registry._tools == {}


class TestToolRegistryRegister:
    """Tests for ToolRegistry.register method."""

    def test_register_adds_tool_to_registry(self):
        """Test that register adds a tool to the registry."""
        registry = ToolRegistry()

        registry.register(add)

        assert len(registry.get_all_tools()) == 1

    def test_register_uses_tool_name_attribute(self):
        """Test that register uses the tool's name attribute."""
        registry = ToolRegistry()

        registry.register(add)

        assert "add" in registry.list_tool_names()

    def test_register_langchain_tool(self):
        """Test registering a LangChain tool decorated with @tool."""

        @tool
        def custom_tool(x: int) -> int:
            """A custom tool for testing."""
            return x * 2

        registry = ToolRegistry()
        registry.register(custom_tool)

        assert "custom_tool" in registry.list_tool_names()

    def test_register_overwrites_existing_tool(self):
        """Test that registering a tool with same name overwrites."""

        @tool
        def my_tool(x: int) -> int:
            """First version."""
            return x

        @tool
        def my_tool_v2(x: int) -> int:  # noqa: F811
            """Second version."""
            return x * 2

        # Manually set name to match
        my_tool_v2.name = "my_tool"

        registry = ToolRegistry()
        registry.register(my_tool)
        registry.register(my_tool_v2)

        assert len(registry.get_all_tools()) == 1

    def test_register_callable_without_name_attribute(self):
        """Test registering a callable that has __name__ but no name attribute."""

        def plain_function(x: int) -> int:
            return x

        registry = ToolRegistry()
        registry.register(plain_function)

        assert "plain_function" in registry.list_tool_names()

    def test_register_mock_tool_with_name(self):
        """Test registering a mock tool with name attribute."""
        mock_tool = MagicMock()
        mock_tool.name = "mock_tool"

        registry = ToolRegistry()
        registry.register(mock_tool)

        assert "mock_tool" in registry.list_tool_names()


class TestToolRegistryRegisterMany:
    """Tests for ToolRegistry.register_many method."""

    def test_register_many_adds_all_tools(self):
        """Test that register_many adds all provided tools."""
        registry = ToolRegistry()

        registry.register_many([add, subtract])

        assert len(registry.get_all_tools()) == 2

    def test_register_many_empty_list(self):
        """Test that register_many with empty list does nothing."""
        registry = ToolRegistry()

        registry.register_many([])

        assert len(registry.get_all_tools()) == 0

    def test_register_many_adds_tools_with_correct_names(self):
        """Test that register_many preserves tool names."""
        registry = ToolRegistry()

        registry.register_many([add, multiply, divide])

        names = registry.list_tool_names()
        assert "add" in names
        assert "multiply" in names
        assert "divide" in names


class TestToolRegistryRegisterDefaults:
    """Tests for ToolRegistry.register_defaults method."""

    def test_register_defaults_adds_calculator_tools(self):
        """Test that register_defaults adds all calculator tools."""
        registry = ToolRegistry()

        registry.register_defaults()

        assert len(registry.get_all_tools()) == len(CALCULATOR_TOOLS)

    def test_register_defaults_includes_add(self):
        """Test that register_defaults includes add tool."""
        registry = ToolRegistry()

        registry.register_defaults()

        assert "add" in registry.list_tool_names()

    def test_register_defaults_includes_subtract(self):
        """Test that register_defaults includes subtract tool."""
        registry = ToolRegistry()

        registry.register_defaults()

        assert "subtract" in registry.list_tool_names()

    def test_register_defaults_includes_multiply(self):
        """Test that register_defaults includes multiply tool."""
        registry = ToolRegistry()

        registry.register_defaults()

        assert "multiply" in registry.list_tool_names()

    def test_register_defaults_includes_divide(self):
        """Test that register_defaults includes divide tool."""
        registry = ToolRegistry()

        registry.register_defaults()

        assert "divide" in registry.list_tool_names()


class TestToolRegistryGetAllTools:
    """Tests for ToolRegistry.get_all_tools method."""

    def test_get_all_tools_returns_list(self):
        """Test that get_all_tools returns a list."""
        registry = ToolRegistry()

        result = registry.get_all_tools()

        assert isinstance(result, list)

    def test_get_all_tools_returns_registered_tools(self):
        """Test that get_all_tools returns all registered tools."""
        registry = ToolRegistry()
        registry.register(add)
        registry.register(subtract)

        result = registry.get_all_tools()

        assert add in result
        assert subtract in result

    def test_get_all_tools_empty_registry(self):
        """Test that get_all_tools returns empty list for empty registry."""
        registry = ToolRegistry()

        result = registry.get_all_tools()

        assert result == []


class TestToolRegistryGetTool:
    """Tests for ToolRegistry.get_tool method."""

    def test_get_tool_returns_registered_tool(self):
        """Test that get_tool returns the correct tool."""
        registry = ToolRegistry()
        registry.register(add)

        result = registry.get_tool("add")

        assert result == add

    def test_get_tool_returns_none_for_unknown(self):
        """Test that get_tool returns None for unknown tool."""
        registry = ToolRegistry()

        result = registry.get_tool("nonexistent")

        assert result is None

    def test_get_tool_after_register_many(self):
        """Test that get_tool works after register_many."""
        registry = ToolRegistry()
        registry.register_many([add, subtract, multiply])

        assert registry.get_tool("add") == add
        assert registry.get_tool("subtract") == subtract
        assert registry.get_tool("multiply") == multiply


class TestToolRegistryListToolNames:
    """Tests for ToolRegistry.list_tool_names method."""

    def test_list_tool_names_returns_list(self):
        """Test that list_tool_names returns a list."""
        registry = ToolRegistry()

        result = registry.list_tool_names()

        assert isinstance(result, list)

    def test_list_tool_names_returns_all_names(self):
        """Test that list_tool_names returns all registered names."""
        registry = ToolRegistry()
        registry.register_many([add, subtract, multiply, divide])

        names = registry.list_tool_names()

        assert len(names) == 4
        assert set(names) == {"add", "subtract", "multiply", "divide"}

    def test_list_tool_names_empty_registry(self):
        """Test that list_tool_names returns empty list for empty registry."""
        registry = ToolRegistry()

        result = registry.list_tool_names()

        assert result == []


class TestGetToolRegistry:
    """Tests for get_tool_registry function."""

    def test_get_tool_registry_returns_registry(self):
        """Test that get_tool_registry returns a ToolRegistry instance."""
        # Note: This uses the global registry which may have state from other tests
        registry = get_tool_registry()

        assert isinstance(registry, ToolRegistry)

    def test_get_tool_registry_has_default_tools(self):
        """Test that global registry has default tools registered."""
        registry = get_tool_registry()

        # Should have calculator tools
        assert len(registry.get_all_tools()) >= len(CALCULATOR_TOOLS)

    def test_get_tool_registry_returns_same_instance(self):
        """Test that get_tool_registry returns the same instance."""
        registry1 = get_tool_registry()
        registry2 = get_tool_registry()

        assert registry1 is registry2

    def test_get_tool_registry_includes_calculator_tools(self):
        """Test that global registry includes all calculator tools."""
        registry = get_tool_registry()
        names = registry.list_tool_names()

        assert "add" in names
        assert "subtract" in names
        assert "multiply" in names
        assert "divide" in names
