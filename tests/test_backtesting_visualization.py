import numpy as np
import pandas as pd
import pytest

from project_structure.backtesting.visualization import (
    plot_allocation_weights,
    plot_cumulative_returns,
    plot_drawdowns,
    plot_rolling_sharpe,
    plot_rolling_volatility,
    plot_strategy_turnover,
)


@pytest.fixture
def sample_results():
    dates = pd.date_range("2024-01-01", periods=4, freq="D")

    return {
        "Strategy A": pd.DataFrame(
            {"net_return": [0.10, -0.05, 0.02, 0.01]},
            index=dates,
        ),
        "Strategy B": pd.DataFrame(
            {"net_return": [0.02, 0.01, -0.03, 0.02]},
            index=dates,
        ),
    }


def test_cumulative_returns_chart_is_created(tmp_path, sample_results):
    path = plot_cumulative_returns(sample_results, tmp_path)

    assert path.exists()
    assert path.name == "backtest_cumulative_returns.png"
    assert path.stat().st_size > 0


def test_drawdown_chart_is_created(tmp_path, sample_results):
    path = plot_drawdowns(sample_results, tmp_path)

    assert path.exists()
    assert path.name == "backtest_drawdowns.png"
    assert path.stat().st_size > 0


def test_empty_results_are_rejected(tmp_path):
    with pytest.raises(ValueError, match="at least one"):
        plot_cumulative_returns({}, tmp_path)


def test_missing_net_returns_are_rejected(tmp_path):
    results = {
        "Strategy A": pd.DataFrame(
            {"gross_return": [0.01, 0.02]}
        )
    }

    with pytest.raises(ValueError, match="net_return"):
        plot_cumulative_returns(results, tmp_path)


def test_non_finite_returns_are_rejected(tmp_path):
    results = {
        "Strategy A": pd.DataFrame(
            {"net_return": [0.01, np.nan]}
        )
    }

    with pytest.raises(ValueError, match="finite"):
        plot_drawdowns(results, tmp_path)

def test_rolling_sharpe_chart_is_created(tmp_path, sample_results):
    path = plot_rolling_sharpe(
        sample_results,
        tmp_path,
        window=3,
    )

    assert path.exists()
    assert path.name == "backtest_rolling_sharpe.png"
    assert path.stat().st_size > 0


def test_rolling_volatility_chart_is_created(tmp_path, sample_results):
    path = plot_rolling_volatility(
        sample_results,
        tmp_path,
        window=3,
    )

    assert path.exists()
    assert path.name == "backtest_rolling_volatility.png"
    assert path.stat().st_size > 0

def test_allocation_chart_is_created(tmp_path, sample_results):
    for frame in sample_results.values():
        frame["weight_SPY"] = [0.60, 0.55, 0.58, 0.62]
        frame["weight_TLT"] = 1.0 - frame["weight_SPY"]

    path = plot_allocation_weights(sample_results, tmp_path)

    assert path.exists()
    assert path.name == "backtest_allocation_weights.png"
    assert path.stat().st_size > 0


def test_turnover_chart_is_created(tmp_path, sample_results):
    for frame in sample_results.values():
        frame["turnover"] = [1.0, 0.0, 0.05, 0.0]

    path = plot_strategy_turnover(sample_results, tmp_path)

    assert path.exists()
    assert path.name == "backtest_strategy_turnover.png"
    assert path.stat().st_size > 0


def test_allocation_chart_rejects_weights_not_summing_to_one(
    tmp_path,
    sample_results,
):
    for frame in sample_results.values():
        frame["weight_SPY"] = 0.60
        frame["weight_TLT"] = 0.30

    with pytest.raises(ValueError, match="sum to 1"):
        plot_allocation_weights(sample_results, tmp_path)