"""Tests for calculator tools."""

from __future__ import annotations

import pytest

from app.tools.calculator import CALCULATOR_TOOLS, add, divide, multiply, subtract


class TestCalculatorTools:
    """Test cases for calculator tool functions."""

    # Test add function
    def test_add_positive_numbers(self):
        """Test addition of two positive numbers."""
        result = add.invoke({"a": 2, "b": 3})
        assert result == 5

    def test_add_negative_numbers(self):
        """Test addition of negative numbers."""
        result = add.invoke({"a": -5, "b": -3})
        assert result == -8

    def test_add_mixed_numbers(self):
        """Test addition of positive and negative numbers."""
        result = add.invoke({"a": 10, "b": -3})
        assert result == 7

    def test_add_floats(self):
        """Test addition of floating point numbers."""
        result = add.invoke({"a": 1.5, "b": 2.5})
        assert result == 4.0

    def test_add_zero(self):
        """Test addition with zero."""
        result = add.invoke({"a": 5, "b": 0})
        assert result == 5

    # Test subtract function
    def test_subtract_positive_numbers(self):
        """Test subtraction of two positive numbers."""
        result = subtract.invoke({"a": 10, "b": 3})
        assert result == 7

    def test_subtract_negative_result(self):
        """Test subtraction resulting in negative number."""
        result = subtract.invoke({"a": 3, "b": 10})
        assert result == -7

    def test_subtract_negative_numbers(self):
        """Test subtraction of negative numbers."""
        result = subtract.invoke({"a": -5, "b": -3})
        assert result == -2

    def test_subtract_floats(self):
        """Test subtraction of floating point numbers."""
        result = subtract.invoke({"a": 5.5, "b": 2.0})
        assert result == 3.5

    def test_subtract_zero(self):
        """Test subtraction with zero."""
        result = subtract.invoke({"a": 5, "b": 0})
        assert result == 5

    # Test multiply function
    def test_multiply_positive_numbers(self):
        """Test multiplication of two positive numbers."""
        result = multiply.invoke({"a": 4, "b": 5})
        assert result == 20

    def test_multiply_by_negative(self):
        """Test multiplication with negative number."""
        result = multiply.invoke({"a": 4, "b": -3})
        assert result == -12

    def test_multiply_negatives(self):
        """Test multiplication of two negative numbers."""
        result = multiply.invoke({"a": -4, "b": -3})
        assert result == 12

    def test_multiply_floats(self):
        """Test multiplication of floating point numbers."""
        result = multiply.invoke({"a": 2.5, "b": 4})
        assert result == 10.0

    def test_multiply_by_zero(self):
        """Test multiplication with zero."""
        result = multiply.invoke({"a": 5, "b": 0})
        assert result == 0

    def test_multiply_by_one(self):
        """Test multiplication by one (identity)."""
        result = multiply.invoke({"a": 42, "b": 1})
        assert result == 42

    # Test divide function
    def test_divide_positive_numbers(self):
        """Test division of two positive numbers."""
        result = divide.invoke({"a": 10, "b": 2})
        assert result == 5

    def test_divide_with_remainder(self):
        """Test division with non-integer result."""
        result = divide.invoke({"a": 7, "b": 2})
        assert result == 3.5

    def test_divide_negative_numbers(self):
        """Test division with negative numbers."""
        result = divide.invoke({"a": -10, "b": 2})
        assert result == -5

    def test_divide_both_negative(self):
        """Test division of two negative numbers."""
        result = divide.invoke({"a": -10, "b": -2})
        assert result == 5

    def test_divide_floats(self):
        """Test division of floating point numbers."""
        result = divide.invoke({"a": 5.0, "b": 2.0})
        assert result == 2.5

    def test_divide_by_zero_raises_error(self):
        """Test that division by zero raises ValueError."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide.invoke({"a": 10, "b": 0})

    def test_divide_zero_by_number(self):
        """Test dividing zero by a number."""
        result = divide.invoke({"a": 0, "b": 5})
        assert result == 0


class TestCalculatorToolsCollection:
    """Test cases for the CALCULATOR_TOOLS collection."""

    def test_calculator_tools_contains_all_tools(self):
        """Test that CALCULATOR_TOOLS contains all expected tools."""
        assert len(CALCULATOR_TOOLS) == 4

    def test_calculator_tools_includes_add(self):
        """Test that add tool is in the collection."""
        assert add in CALCULATOR_TOOLS

    def test_calculator_tools_includes_subtract(self):
        """Test that subtract tool is in the collection."""
        assert subtract in CALCULATOR_TOOLS

    def test_calculator_tools_includes_multiply(self):
        """Test that multiply tool is in the collection."""
        assert multiply in CALCULATOR_TOOLS

    def test_calculator_tools_includes_divide(self):
        """Test that divide tool is in the collection."""
        assert divide in CALCULATOR_TOOLS


class TestToolMetadata:
    """Test cases for tool metadata."""

    def test_add_tool_has_name(self):
        """Test that add tool has correct name."""
        assert add.name == "add"

    def test_subtract_tool_has_name(self):
        """Test that subtract tool has correct name."""
        assert subtract.name == "subtract"

    def test_multiply_tool_has_name(self):
        """Test that multiply tool has correct name."""
        assert multiply.name == "multiply"

    def test_divide_tool_has_name(self):
        """Test that divide tool has correct name."""
        assert divide.name == "divide"

    def test_add_tool_has_description(self):
        """Test that add tool has description."""
        assert add.description is not None
        assert len(add.description) > 0

    def test_divide_tool_has_description(self):
        """Test that divide tool has description."""
        assert divide.description is not None
        assert len(divide.description) > 0
