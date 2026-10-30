import numpy as np
import pandas as pd
import pytest
from project_structure.backtesting.custom_portfolio import (run_custom_portfolio_backtest)

@pytest.fixture
def sample_returns():
    dates = pd.bdate_range("2020-01-01", periods=80)
    return pd.DataFrame(
        {
            "SPY": np.linspace(-0.01, 0.012, 80),
            "TLT": np.linspace(0.004, -0.003, 80),
        },
        index=dates,
    )


def test_custom_backtest_returns_out_of_sample_results(sample_returns):
    results, metrics, drawdown = run_custom_portfolio_backtest(
        sample_returns,
        {"SPY": 0.6, "TLT": 0.4},
        lookback=20,
        rebalance_every=5,
        transaction_cost_bps=10,
    )

    assert len(results) == len(sample_returns) - 20
    assert results.index.min() == sample_returns.index[20]
    assert {"gross_return", "net_return", "turnover"} <= set(results.columns)
    assert "weight_SPY" in results.columns
    assert "weight_TLT" in results.columns
    assert "sharpe_ratio" in metrics
    assert len(drawdown) == len(results)


def test_custom_backtest_applies_requested_weights_initially(sample_returns):
    results, _, _ = run_custom_portfolio_backtest(
        sample_returns,
        {"SPY": 0.6, "TLT": 0.4},
        lookback=20,
        rebalance_every=5,
    )

    assert results["weight_SPY"].iloc[0] == pytest.approx(0.6)
    assert results["weight_TLT"].iloc[0] == pytest.approx(0.4)


def test_custom_backtest_rejects_weights_not_summing_to_one(sample_returns):
    with pytest.raises(ValueError, match="sum to 1"):
        run_custom_portfolio_backtest(
            sample_returns,
            {"SPY": 0.6, "TLT": 0.3},
            lookback=20,
        )


def test_custom_backtest_rejects_mismatched_assets(sample_returns):
    with pytest.raises(ValueError, match="must match"):
        run_custom_portfolio_backtest(
            sample_returns,
            {"SPY": 0.6, "QQQ": 0.4},
            lookback=20,
        )


def test_custom_backtest_charges_initial_transaction_cost(sample_returns):
    results, _, _ = run_custom_portfolio_backtest(
        sample_returns,
        {"SPY": 0.6, "TLT": 0.4},
        lookback=20,
        transaction_cost_bps=10,
    )

    assert results["turnover"].iloc[0] == pytest.approx(1.0)
    assert results["transaction_cost"].iloc[0] == pytest.approx(0.001)