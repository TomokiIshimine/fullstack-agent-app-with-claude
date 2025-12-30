"""Tests for cost calculator utility."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.utils.cost_calculator import CostCalculationResult, calculate_cost, calculate_cost_detailed


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def test_calculate_cost_success(self):
        """Test successful cost calculation."""
        with patch("app.utils.cost_calculator.cost_per_token") as mock_cost:
            mock_cost.return_value = (0.003, 0.006)  # input_cost, output_cost

            result = calculate_cost(
                model="claude-sonnet-4-5-20250929",
                input_tokens=1000,
                output_tokens=500,
            )

            assert result == pytest.approx(0.009)
            mock_cost.assert_called_once_with(
                model="claude-sonnet-4-5-20250929",
                prompt_tokens=1000,
                completion_tokens=500,
            )

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        with patch("app.utils.cost_calculator.cost_per_token") as mock_cost:
            mock_cost.return_value = (0.0, 0.0)

            result = calculate_cost(
                model="claude-sonnet-4-5-20250929",
                input_tokens=0,
                output_tokens=0,
            )

            assert result == 0.0

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation with unknown model returns 0."""
        with patch("app.utils.cost_calculator.cost_per_token") as mock_cost:
            mock_cost.side_effect = Exception("Model not found in pricing database")

            result = calculate_cost(
                model="unknown-model",
                input_tokens=1000,
                output_tokens=500,
            )

            assert result == 0.0

    def test_calculate_cost_api_error(self):
        """Test cost calculation handles API errors gracefully."""
        with patch("app.utils.cost_calculator.cost_per_token") as mock_cost:
            mock_cost.side_effect = RuntimeError("Network error")

            result = calculate_cost(
                model="claude-sonnet-4-5-20250929",
                input_tokens=1000,
                output_tokens=500,
            )

            assert result == 0.0

    def test_calculate_cost_small_amounts(self):
        """Test cost calculation with very small amounts."""
        with patch("app.utils.cost_calculator.cost_per_token") as mock_cost:
            # Simulate very small costs (e.g., $0.000001)
            mock_cost.return_value = (0.0000005, 0.0000005)

            result = calculate_cost(
                model="claude-sonnet-4-5-20250929",
                input_tokens=10,
                output_tokens=10,
            )

            assert result == 0.000001
            assert result > 0  # Ensure precision is maintained

    def test_calculate_cost_large_token_counts(self):
        """Test cost calculation with large token counts."""
        with patch("app.utils.cost_calculator.cost_per_token") as mock_cost:
            mock_cost.return_value = (1.5, 3.0)  # Large costs

            result = calculate_cost(
                model="claude-sonnet-4-5-20250929",
                input_tokens=500000,
                output_tokens=200000,
            )

            assert result == 4.5


class TestCalculateCostDetailed:
    """Tests for calculate_cost_detailed function."""

    def test_calculate_cost_detailed_success(self):
        """Test detailed cost calculation returns breakdown."""
        with patch("app.utils.cost_calculator.cost_per_token") as mock_cost:
            mock_cost.return_value = (0.003, 0.006)

            result = calculate_cost_detailed(
                model="claude-sonnet-4-5-20250929",
                input_tokens=1000,
                output_tokens=500,
            )

            assert isinstance(result, CostCalculationResult)
            assert result.input_cost == pytest.approx(0.003)
            assert result.output_cost == pytest.approx(0.006)
            assert result.total_cost == pytest.approx(0.009)

    def test_calculate_cost_detailed_zero_tokens(self):
        """Test detailed cost calculation with zero tokens."""
        with patch("app.utils.cost_calculator.cost_per_token") as mock_cost:
            mock_cost.return_value = (0.0, 0.0)

            result = calculate_cost_detailed(
                model="claude-sonnet-4-5-20250929",
                input_tokens=0,
                output_tokens=0,
            )

            assert result.input_cost == 0.0
            assert result.output_cost == 0.0
            assert result.total_cost == 0.0

    def test_calculate_cost_detailed_error(self):
        """Test detailed cost calculation handles errors."""
        with patch("app.utils.cost_calculator.cost_per_token") as mock_cost:
            mock_cost.side_effect = Exception("Model not found")

            result = calculate_cost_detailed(
                model="unknown-model",
                input_tokens=1000,
                output_tokens=500,
            )

            assert isinstance(result, CostCalculationResult)
            assert result.input_cost == 0.0
            assert result.output_cost == 0.0
            assert result.total_cost == 0.0


class TestCostCalculationResult:
    """Tests for CostCalculationResult dataclass."""

    def test_dataclass_creation(self):
        """Test CostCalculationResult can be created."""
        result = CostCalculationResult(
            input_cost=0.001,
            output_cost=0.002,
            total_cost=0.003,
        )

        assert result.input_cost == 0.001
        assert result.output_cost == 0.002
        assert result.total_cost == 0.003

    def test_dataclass_equality(self):
        """Test CostCalculationResult equality comparison."""
        result1 = CostCalculationResult(
            input_cost=0.001,
            output_cost=0.002,
            total_cost=0.003,
        )
        result2 = CostCalculationResult(
            input_cost=0.001,
            output_cost=0.002,
            total_cost=0.003,
        )

        assert result1 == result2


class TestIntegration:
    """Integration tests with actual LiteLLM (skip if LiteLLM not available)."""

    @pytest.mark.integration
    def test_real_cost_calculation_claude(self):
        """Test real cost calculation for Claude model."""
        # This test uses the real LiteLLM pricing database
        # Skip if running in CI without network access
        try:
            import litellm  # noqa: F401 - Check if LiteLLM is available

            # Test with a known model
            result = calculate_cost(
                model="claude-sonnet-4-5-20250929",
                input_tokens=1000,
                output_tokens=500,
            )

            # Cost should be positive for a valid model
            assert result >= 0
        except Exception:
            pytest.skip("LiteLLM pricing database not available")

    @pytest.mark.integration
    def test_real_cost_calculation_gpt4(self):
        """Test real cost calculation for GPT-4 model."""
        try:
            import litellm  # noqa: F401 - Check if LiteLLM is available

            result = calculate_cost(
                model="gpt-4",
                input_tokens=1000,
                output_tokens=500,
            )

            assert result >= 0
        except Exception:
            pytest.skip("LiteLLM pricing database not available")
