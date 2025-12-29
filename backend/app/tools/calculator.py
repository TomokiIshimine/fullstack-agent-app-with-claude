"""Calculator tools for basic arithmetic operations."""

from langchain_core.tools import tool


@tool
def add(a: float, b: float) -> float:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of a and b
    """
    return a + b


@tool
def subtract(a: float, b: float) -> float:
    """Subtract the second number from the first.

    Args:
        a: First number
        b: Second number

    Returns:
        The difference (a - b)
    """
    return a - b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        The product of a and b
    """
    return a * b


@tool
def divide(a: float, b: float) -> float:
    """Divide the first number by the second.

    Args:
        a: Numerator
        b: Denominator (must not be zero)

    Returns:
        The quotient (a / b)

    Raises:
        ValueError: If b is zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


CALCULATOR_TOOLS = [add, subtract, multiply, divide]

__all__ = ["add", "subtract", "multiply", "divide", "CALCULATOR_TOOLS"]
