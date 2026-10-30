import numpy as np
import pandas as pd
import pytest

from project_structure.backtesting.engine import run_backtest


def make_returns() -> pd.DataFrame:
    """Create a small deterministic returns dataset."""
    dates = pd.date_range("2025-01-01", periods=6, freq="D")
    return pd.DataFrame(
        {
            "A": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06],
            "B": [0.00, 0.01, 0.02, 0.01, 0.00, -0.01],
        },
        index=dates,
    )


def equal_weight_strategy(history: pd.DataFrame) -> pd.Series:
    """Allocate equally across all available assets."""
    return pd.Series(
        1.0 / len(history.columns),
        index=history.columns,
    )


def test_backtest_excludes_training_period():
    returns = make_returns()

    results = run_backtest(
        returns,
        equal_weight_strategy,
        lookback=3,
        rebalance_every=2,
        transaction_cost_bps=0,
    )

    assert len(results) == 3
    assert results.index.equals(returns.index[3:])


def test_backtest_calculates_portfolio_returns():
    returns = make_returns()

    results = run_backtest(
        returns,
        equal_weight_strategy,
        lookback=3,
        rebalance_every=1,
        transaction_cost_bps=0,
    )

    expected = returns.iloc[3:].mean(axis=1)
    expected.index.name = "Date"

    pd.testing.assert_series_equal(
        results["gross_return"],
        expected.rename("gross_return"),
    )
    pd.testing.assert_series_equal(
        results["net_return"],
        expected.rename("net_return"),
    )


def test_initial_transaction_cost_is_applied():
    returns = make_returns()

    results = run_backtest(
        returns,
        equal_weight_strategy,
        lookback=3,
        transaction_cost_bps=10,
    )

    first = results.iloc[0]

    assert first["turnover"] == pytest.approx(1.0)
    assert first["transaction_cost"] == pytest.approx(0.001)
    assert first["net_return"] == pytest.approx(
        (1 - 0.001) * (1 + first["gross_return"]) - 1
    )


def test_transaction_cost_is_not_charged_every_day():
    returns = make_returns()

    results = run_backtest(
        returns,
        equal_weight_strategy,
        lookback=3,
        rebalance_every=2,
        transaction_cost_bps=10,
    )

    assert results["transaction_cost"].iloc[0] == pytest.approx(0.001)
    assert results["transaction_cost"].iloc[1] == pytest.approx(0.0)
    assert results["transaction_cost"].iloc[2] == pytest.approx(
        10 / 10_000 * results["turnover"].iloc[2]
    )
    assert results["transaction_cost"].iloc[2] > 0


def test_strategy_receives_only_past_returns():
    returns = make_returns()
    observed_windows = []

    def recording_strategy(history: pd.DataFrame) -> pd.Series:
        observed_windows.append(history.copy())
        return equal_weight_strategy(history)

    run_backtest(
        returns,
        recording_strategy,
        lookback=3,
        rebalance_every=2,
        transaction_cost_bps=0,
    )

    assert len(observed_windows) == 2

    # First test return is on row 3; training ends at row 2.
    assert observed_windows[0].index.equals(returns.index[:3])

    # The next rebalance occurs two test observations later.
    assert observed_windows[1].index.equals(returns.index[2:5])

    for window in observed_windows:
        assert window.index.max() < returns.index[
            returns.index.get_loc(window.index.max()) + 1
        ]


def test_rebalancing_turnover_is_calculated():
    returns = make_returns()

    def switching_strategy(history: pd.DataFrame) -> pd.Series:
        if history.index[-1] == returns.index[2]:
            return pd.Series({"A": 1.0, "B": 0.0})
        return pd.Series({"A": 0.0, "B": 1.0})

    results = run_backtest(
        returns,
        switching_strategy,
        lookback=3,
        rebalance_every=1,
        transaction_cost_bps=10,
    )

    assert results["turnover"].iloc[0] == pytest.approx(1.0)
    assert results["turnover"].iloc[1] == pytest.approx(2.0)
    assert results["transaction_cost"].iloc[1] == pytest.approx(0.002)


@pytest.mark.parametrize("lookback", [0, 1, -1])
def test_invalid_lookback_is_rejected(lookback):
    with pytest.raises(ValueError):
        run_backtest(
            make_returns(),
            equal_weight_strategy,
            lookback=lookback,
        )


def test_missing_returns_are_rejected():
    returns = make_returns()
    returns.iloc[2, 0] = np.nan

    with pytest.raises(ValueError, match="missing values"):
        run_backtest(returns, equal_weight_strategy, lookback=2)


def test_invalid_weights_are_rejected():
    returns = make_returns()

    def invalid_strategy(history: pd.DataFrame) -> pd.Series:
        return pd.Series({"A": 0.8, "B": 0.8})

    with pytest.raises(ValueError, match="sum to 1"):
        run_backtest(
            returns,
            invalid_strategy,
            lookback=2,
        )


def test_insufficient_data_is_rejected():
    with pytest.raises(ValueError, match="more observations"):
        run_backtest(
            make_returns(),
            equal_weight_strategy,
            lookback=6,
        )

def test_weights_drift_between_rebalances():
    """Portfolio weights should change when asset returns differ."""
    returns = pd.DataFrame(
        {
            "A": [0.00, 0.00, 0.10, 0.00],
            "B": [0.00, 0.00, 0.00, 0.00],
        },
        index=pd.date_range("2024-01-01", periods=4, freq="D"),
    )

    def equal_weights(history):
        return pd.Series({"A": 0.5, "B": 0.5})

    results = run_backtest(
        asset_returns=returns,
        strategy=equal_weights,
        lookback=2,
        rebalance_every=3,
        transaction_cost_bps=0,
    )

    # The first evaluated day starts at 50/50 and A rises by 10%.
    assert results.iloc[0]["weight_A"] == pytest.approx(0.5)
    assert results.iloc[0]["weight_B"] == pytest.approx(0.5)

    # On the next day, the holdings have drifted to 55/45. No rebalance yet.
    assert results.iloc[1]["weight_A"] == pytest.approx(0.55 / 1.05)
    assert results.iloc[1]["weight_B"] == pytest.approx(0.5 / 1.05)


def test_turnover_uses_drifted_weights_at_rebalance():
    """Rebalance turnover should compare targets with current holdings."""
    returns = pd.DataFrame(
        {
            "A": [0.00, 0.00, 0.10, 0.00, 0.00],
            "B": [0.00, 0.00, 0.00, 0.00, 0.00],
        },
        index=pd.date_range("2024-01-01", periods=5, freq="D"),
    )

    def equal_weights(history):
        return pd.Series({"A": 0.5, "B": 0.5})

    results = run_backtest(
        asset_returns=returns,
        strategy=equal_weights,
        lookback=2,
        rebalance_every=2,
        transaction_cost_bps=0,
    )

    # First out-of-sample day establishes the portfolio.
    assert results.iloc[0]["turnover"] == pytest.approx(1.0)

    # The next rebalance occurs after A's gain has changed its weight.
    expected_drifted_a = 0.55 / 1.05
    expected_drifted_b = 0.5 / 1.05
    expected_turnover = (
        abs(0.5 - expected_drifted_a)
        + abs(0.5 - expected_drifted_b)
    )

    assert results.iloc[2]["turnover"] == pytest.approx(expected_turnover)
    assert results.iloc[2]["turnover"] < 1.0