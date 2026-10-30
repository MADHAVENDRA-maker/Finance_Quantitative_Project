import numpy as np
import pandas as pd
import pytest
from project_structure.backtesting.engine import run_backtest
from project_structure.backtesting.strategies import custom_weight_strategy


def make_returns() -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=40, freq="B")
    rng = np.random.default_rng(42)

    return pd.DataFrame(
        {
            "SPY": rng.normal(0.0005, 0.01, len(dates)),
            "TLT": rng.normal(0.0002, 0.005, len(dates)),
            "GLD": rng.normal(0.0003, 0.007, len(dates)),
        },
        index=dates,
    )


def test_custom_weights_are_preserved():
    strategy = custom_weight_strategy({"SPY": 0.6, "TLT": 0.4})
    history = make_returns()[["SPY", "TLT"]]

    weights = strategy(history)

    assert weights["SPY"] == pytest.approx(0.6)
    assert weights["TLT"] == pytest.approx(0.4)
    assert weights.sum() == pytest.approx(1.0)


def test_custom_weights_align_to_asset_column_order():
    strategy = custom_weight_strategy({"SPY": 0.6, "TLT": 0.4})
    history = make_returns()[["TLT", "SPY"]]

    weights = strategy(history)

    assert list(weights.index) == ["TLT", "SPY"]
    assert weights["TLT"] == pytest.approx(0.4)
    assert weights["SPY"] == pytest.approx(0.6)


@pytest.mark.parametrize(
    "weights",
    [
        {},
        {"SPY": 0.6, "TLT": 0.3},
        {"SPY": -0.1, "TLT": 1.1},
        {"SPY": float("nan"), "TLT": 1.0},
    ],
)
def test_invalid_custom_weights_are_rejected(weights):
    with pytest.raises((ValueError, TypeError)):
        custom_weight_strategy(weights)


def test_custom_strategy_rejects_mismatched_assets():
    strategy = custom_weight_strategy({"SPY": 0.6, "TLT": 0.4})
    history = make_returns()[["SPY", "GLD"]]

    with pytest.raises(ValueError, match="must match"):
        strategy(history)


def test_custom_strategy_runs_in_backtest():
    returns = make_returns()[["SPY", "TLT"]]
    strategy = custom_weight_strategy({"SPY": 0.6, "TLT": 0.4})

    results = run_backtest(
        asset_returns=returns,
        strategy=strategy,
        lookback=20,
        rebalance_every=5,
        transaction_cost_bps=10,
    )

    assert len(results) == 20
    assert results["net_return"].notna().all()
    assert results["gross_return"].notna().all()
    assert (results["transaction_cost"] >= 0).all()

    # Target weights are applied at the start of the backtest.
    assert results.iloc[0]["weight_SPY"] == pytest.approx(0.6)
    assert results.iloc[0]["weight_TLT"] == pytest.approx(0.4)

    # Portfolio weights must sum to 1 at each period's start.
    weights = results[["weight_SPY", "weight_TLT"]]
    np.testing.assert_allclose(weights.sum(axis=1), 1.0)