"""Cost calculator utility using LiteLLM for multi-provider support."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from litellm import cost_per_token

logger = logging.getLogger(__name__)


@dataclass
class CostCalculationResult:
    """Result of cost calculation."""

    input_cost: float
    output_cost: float
    total_cost: float


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """
    Calculate the cost for a given model and token usage using LiteLLM.

    LiteLLM maintains an up-to-date pricing database for all major LLM providers,
    eliminating the need to manually maintain pricing tables.

    Args:
        model: Model name (e.g., "claude-sonnet-4-5-20250929", "gpt-4")
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens

    Returns:
        Total cost in USD

    Example:
        >>> cost = calculate_cost("claude-sonnet-4-5-20250929", 1000, 500)
        >>> print(f"${cost:.6f}")
        $0.010500
    """
    try:
        input_cost, output_cost = cost_per_token(
            model=model,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
        )
        total_cost = input_cost + output_cost
        logger.debug(
            f"Cost calculated for {model}: "
            f"input={input_tokens} tokens (${input_cost:.6f}), "
            f"output={output_tokens} tokens (${output_cost:.6f}), "
            f"total=${total_cost:.6f}"
        )
        return total_cost
    except Exception as e:
        logger.warning(f"Failed to calculate cost for model {model}: {e}")
        # Return 0 if cost calculation fails (model not in LiteLLM's database)
        return 0.0


def calculate_cost_detailed(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> CostCalculationResult:
    """
    Calculate detailed cost breakdown for a given model and token usage.

    Args:
        model: Model name
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens

    Returns:
        CostCalculationResult with input_cost, output_cost, and total_cost
    """
    try:
        input_cost, output_cost = cost_per_token(
            model=model,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
        )
        return CostCalculationResult(
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
        )
    except Exception as e:
        logger.warning(f"Failed to calculate cost for model {model}: {e}")
        return CostCalculationResult(
            input_cost=0.0,
            output_cost=0.0,
            total_cost=0.0,
        )


__all__ = ["calculate_cost", "calculate_cost_detailed", "CostCalculationResult"]
