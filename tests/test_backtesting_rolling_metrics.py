import numpy as np
import pandas as pd
import pytest

from project_structure.backtesting.rolling_metrics import (
    calculate_rolling_sharpe,
    calculate_rolling_volatility,
)


@pytest.fixture
def sample_returns():
    return pd.Series(
        [0.01, -0.005, 0.02, 0.003, -0.01, 0.015],
        index=pd.date_range("2024-01-01", periods=6, freq="D"),
        name="net_return",
    )


def test_rolling_volatility_matches_manual_calculation(sample_returns):
    result = calculate_rolling_volatility(sample_returns, window=3)

    expected = sample_returns.iloc[:3].std(ddof=1) * np.sqrt(252)

    assert result.iloc[:2].isna().all()
    assert result.iloc[2] == pytest.approx(expected)
    assert result.name == "rolling_volatility"


def test_rolling_sharpe_matches_manual_calculation(sample_returns):
    result = calculate_rolling_sharpe(sample_returns, window=3)

    first_window = sample_returns.iloc[:3]
    expected = (
        first_window.mean()
        / first_window.std(ddof=1)
        * np.sqrt(252)
    )

    assert result.iloc[:2].isna().all()
    assert result.iloc[2] == pytest.approx(expected)
    assert result.name == "rolling_sharpe"


def test_rolling_sharpe_accepts_annual_risk_free_rate(sample_returns):
    result = calculate_rolling_sharpe(
        sample_returns,
        window=3,
        risk_free_rate=0.04,
    )

    assert result.iloc[2:].notna().all()


def test_window_must_be_at_least_two(sample_returns):
    with pytest.raises(ValueError, match="at least 2"):
        calculate_rolling_volatility(sample_returns, window=1)


def test_non_finite_returns_are_rejected():
    returns = pd.Series([0.01, np.nan, 0.02])

    with pytest.raises(ValueError, match="finite"):
        calculate_rolling_sharpe(returns, window=2)


def test_returns_below_minus_100_percent_are_rejected():
    returns = pd.Series([0.01, -1.01, 0.02])

    with pytest.raises(ValueError, match="below -100%"):
        calculate_rolling_volatility(returns, window=2)


def test_constant_returns_produce_nan_sharpe():
    returns = pd.Series([0.01] * 5)

    result = calculate_rolling_sharpe(returns, window=3)

    assert result.iloc[2:].isna().all()