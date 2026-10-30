import numpy as np
import pandas as pd
import pytest

from project_structure.features.performance import calculate_performance_metrics, compare_assets


def test_total_return_is_compounded() -> None:
    returns = pd.Series([0.10, -0.10])

    metrics = calculate_performance_metrics(returns)

    assert metrics["total_return"] == pytest.approx(-0.01)


def test_annualized_return_uses_compounding() -> None:
    returns = pd.Series([0.01, 0.01])

    metrics = calculate_performance_metrics(
        returns,
        periods_per_year=2,
    )

    assert metrics["annualized_return"] == pytest.approx(0.0201)


def test_annualized_volatility_is_calculated() -> None:
    returns = pd.Series([0.01, -0.01, 0.02, -0.02])

    metrics = calculate_performance_metrics(
        returns,
        periods_per_year=4,
    )

    assert metrics["annualized_volatility"] == pytest.approx(
        returns.std(ddof=1) * np.sqrt(4)
    )


def test_maximum_drawdown_includes_initial_wealth() -> None:
    returns = pd.Series([0.10, -0.20, 0.05])

    metrics = calculate_performance_metrics(returns)

    assert metrics["maximum_drawdown"] == pytest.approx(-0.20)


def test_zero_volatility_produces_nan_sharpe() -> None:
    returns = pd.Series([0.01, 0.01, 0.01])

    metrics = calculate_performance_metrics(returns)

    assert np.isnan(metrics["sharpe_ratio"])


def test_missing_returns_are_rejected() -> None:
    with pytest.raises(ValueError, match="missing values"):
        calculate_performance_metrics(pd.Series([0.01, np.nan]))


def test_returns_below_minus_one_are_rejected() -> None:
    with pytest.raises(ValueError, match="less than -100%"):
        calculate_performance_metrics(pd.Series([0.01, -1.01]))


def test_compare_assets_returns_one_row_per_asset() -> None:
    returns = pd.DataFrame(
        {
            "SPY": [0.01, -0.005, 0.02],
            "TLT": [0.005, 0.01, -0.002],
        }
    )

    result = compare_assets(returns)

    assert list(result.index) == ["SPY", "TLT"]
    assert "annualized_volatility" in result.columns
    assert "maximum_drawdown" in result.columns


def test_comparison_rejects_missing_observations() -> None:
    returns = pd.DataFrame(
        {
            "SPY": [0.01, 0.02],
            "TLT": [0.01, np.nan],
        }
    )

    with pytest.raises(ValueError, match="missing observations"):
        compare_assets(returns)