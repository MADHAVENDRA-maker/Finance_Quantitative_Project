import numpy as np
import pandas as pd
import pytest

from project_structure.backtesting.engine import run_backtest
from project_structure.backtesting.strategies import (
    equal_weight_strategy,
    maximum_sharpe_strategy,
    minimum_variance_strategy,
)


@pytest.fixture
def historical_returns() -> pd.DataFrame:
    """Generate deterministic returns with different asset characteristics."""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2020-01-01", periods=80, freq="B")

    asset_a = rng.normal(0.0008, 0.010, len(dates))
    asset_b = rng.normal(0.0003, 0.006, len(dates))

    return pd.DataFrame(
        {"A": asset_a, "B": asset_b},
        index=dates,
    )


@pytest.mark.parametrize(
    "strategy",
    [
        equal_weight_strategy,
        minimum_variance_strategy,
        maximum_sharpe_strategy,
    ],
)
def test_strategy_returns_valid_weights(historical_returns, strategy):
    weights = strategy(historical_returns)

    assert isinstance(weights, pd.Series)
    assert set(weights.index) == set(historical_returns.columns)
    assert np.isfinite(weights.to_numpy()).all()
    assert (weights >= 0).all()
    assert (weights <= 1).all()
    assert weights.sum() == pytest.approx(1.0)


def test_equal_weight_strategy(historical_returns):
    weights = equal_weight_strategy(historical_returns)

    assert weights["A"] == pytest.approx(0.5)
    assert weights["B"] == pytest.approx(0.5)


def test_strategies_reject_empty_history():
    empty = pd.DataFrame(columns=["A", "B"])

    for strategy in (
        equal_weight_strategy,
        minimum_variance_strategy,
        maximum_sharpe_strategy,
    ):
        with pytest.raises(ValueError, match="cannot be empty"):
            strategy(empty)


def test_strategies_work_with_backtesting_engine(historical_returns):
    for strategy in (
        equal_weight_strategy,
        minimum_variance_strategy,
        maximum_sharpe_strategy,
    ):
        results = run_backtest(
            asset_returns=historical_returns,
            strategy=strategy,
            lookback=40,
            rebalance_every=10,
            transaction_cost_bps=10,
        )

        assert len(results) == 40
        assert results["net_return"].notna().all()
        assert results["gross_return"].notna().all()
        assert (results["transaction_cost"] >= 0).all()