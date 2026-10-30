import numpy as np
import pandas as pd
import pytest

import stateful_walk_forward_validation as swf


def make_candidate(
    dates: pd.DatetimeIndex,
    daily_return: float,
) -> pd.DataFrame:
    """Build a minimal candidate backtest with deterministic returns."""
    return pd.DataFrame(
        {"net_return": daily_return},
        index=dates,
    )


def make_decisions(
    years: list[int],
    intervals: list[int],
    strategy: str = "Equal Weight",
) -> pd.DataFrame:
    """Build yearly rebalance decisions for a single strategy."""
    return pd.DataFrame(
        {
            "strategy": [strategy] * len(years),
            "test_year": years,
            "selected_rebalance_every": intervals,
            "selection_sharpe": [0.5] * len(years),
            "selection_observations": [100] * len(years),
            "transaction_cost_bps": [
                swf.TRANSACTION_COST_BPS
            ] * len(years),
        }
    )


def equal_weight_strategy(history: pd.DataFrame) -> pd.Series:
    """Return equal weights for the assets in the supplied history."""
    return pd.Series(
        1.0 / len(history.columns),
        index=history.columns,
    )


def test_select_interval_uses_only_prior_years():
    """Changing future candidate returns must not affect an earlier choice."""
    dates = pd.date_range("2018-01-01", "2022-12-31", freq="B")

    candidates = {
        ("Equal Weight", 5): make_candidate(dates, 0.001),
        ("Equal Weight", 21): make_candidate(dates, 0.0005),
        ("Equal Weight", 63): make_candidate(dates, 0.0002),
    }

    original = swf.select_interval(
        "Equal Weight",
        2021,
        candidates,
    )

    # Change only data from the selection year onward.
    modified = {
        key: frame.copy()
        for key, frame in candidates.items()
    }

    for frame in modified.values():
        future_mask = frame.index.year >= 2021
        frame.loc[future_mask, "net_return"] = np.nan

    changed = swf.select_interval(
        "Equal Weight",
        2021,
        modified,
    )

    assert original["interval"] == changed["interval"]
    assert original["score"] == pytest.approx(changed["score"])
    assert original["observations"] == changed["observations"]


def test_select_interval_rejects_missing_historical_candidates():
    """Selection must fail clearly if no candidate has usable history."""
    dates = pd.date_range("2020-01-01", "2020-12-31", freq="B")

    candidates = {
        ("Equal Weight", interval): make_candidate(dates, np.nan)
        for interval in swf.REBALANCE_INTERVALS
    }

    with pytest.raises((ValueError, RuntimeError)):
        swf.select_interval(
            "Equal Weight",
            2021,
            candidates,
        )


def test_make_yearly_decisions_uses_prior_years_only():
    """Yearly decisions should contain a growing historical selection window."""
    dates = pd.date_range("2018-01-01", "2022-12-31", freq="B")

    candidates = {}
    for strategy in swf.STRATEGIES:
        for interval in swf.REBALANCE_INTERVALS:
            candidates[(strategy, interval)] = make_candidate(
                dates,
                0.0004 + interval / 1_000_000,
            )

    decisions = swf.make_yearly_decisions(candidates)

    assert not decisions.empty
    assert {
        "strategy",
        "test_year",
        "selected_rebalance_every",
        "selection_sharpe",
        "selection_observations",
    }.issubset(decisions.columns)

    assert decisions["selected_rebalance_every"].isin(
        swf.REBALANCE_INTERVALS
    ).all()

    for _, decision in decisions.iterrows():
        test_year = int(decision["test_year"])
        strategy = decision["strategy"]

        historical = candidates[
            (strategy, int(decision["selected_rebalance_every"]))
        ]
        expected_observations = (
            historical.index.year < test_year
        ).sum()

        assert decision["selection_observations"] == expected_observations


def test_stateful_simulation_has_valid_returns_and_weights(monkeypatch):
    """Simulated returns and reported portfolio weights must be valid."""
    monkeypatch.setattr(swf, "LOOKBACK", 5)

    dates = pd.bdate_range("2018-01-01", "2021-12-31")
    asset_returns = pd.DataFrame(
        {
            "ASSET_A": 0.001,
            "ASSET_B": -0.0002,
        },
        index=dates,
    )

    decisions = make_decisions(
        years=[2020, 2021],
        intervals=[5, 21],
    )

    results = swf.simulate_stateful_portfolio(
        asset_returns=asset_returns,
        strategy_name="Equal Weight",
        strategy_function=equal_weight_strategy,
        decisions=decisions,
    )

    assert not results.empty

    required_columns = {
        "Date",
        "strategy",
        "selected_rebalance_every",
        "gross_return",
        "net_return",
        "turnover",
        "transaction_cost",
        "rebalanced",
        "weight_ASSET_A",
        "weight_ASSET_B",
    }
    assert required_columns.issubset(results.columns)

    assert pd.to_datetime(results["Date"]).dt.year.min() >= 2020
    assert np.isfinite(results["gross_return"]).all()
    assert np.isfinite(results["net_return"]).all()
    assert (results["turnover"] >= 0).all()
    assert (results["transaction_cost"] >= 0).all()

    weights = results[["weight_ASSET_A", "weight_ASSET_B"]]

    assert np.isfinite(weights.to_numpy()).all()
    assert (weights >= -1e-10).all().all()
    assert np.allclose(weights.sum(axis=1), 1.0, atol=1e-8)


def test_stateful_simulation_applies_new_interval_at_year_change(
    monkeypatch,
):
    """A changed yearly interval should trigger a rebalance."""
    monkeypatch.setattr(swf, "LOOKBACK", 5)

    dates = pd.bdate_range("2018-01-01", "2021-12-31")
    asset_returns = pd.DataFrame(
        {
            "ASSET_A": 0.0005,
            "ASSET_B": 0.0001,
        },
        index=dates,
    )

    decisions = make_decisions(
        years=[2020, 2021],
        intervals=[5, 21],
    )

    results = swf.simulate_stateful_portfolio(
        asset_returns=asset_returns,
        strategy_name="Equal Weight",
        strategy_function=equal_weight_strategy,
        decisions=decisions,
    )

    results = results.copy()
    results["Date"] = pd.to_datetime(results["Date"])

    first_2021 = results.loc[
        results["Date"].dt.year == 2021
    ].iloc[0]

    assert first_2021["selected_rebalance_every"] == 21
    assert bool(first_2021["rebalanced"])


def test_transaction_cost_and_net_return_accounting(
    monkeypatch,
):
    """Net returns should match the stated transaction-cost convention."""
    monkeypatch.setattr(swf, "LOOKBACK", 5)

    dates = pd.bdate_range("2018-01-01", "2021-12-31")
    asset_returns = pd.DataFrame(
        {
            "ASSET_A": 0.001,
            "ASSET_B": -0.0005,
        },
        index=dates,
    )

    decisions = make_decisions(
        years=[2020, 2021],
        intervals=[5, 5],
    )

    results = swf.simulate_stateful_portfolio(
        asset_returns=asset_returns,
        strategy_name="Equal Weight",
        strategy_function=equal_weight_strategy,
        decisions=decisions,
    )

    expected_cost = (
        results["turnover"]
        * swf.TRANSACTION_COST_BPS
        / 10_000.0
    )
    expected_net_return = (
        (1.0 - expected_cost)
        * (1.0 + results["gross_return"])
        - 1.0
    )

    assert np.allclose(
        results["transaction_cost"],
        expected_cost,
        atol=1e-10,
    )
    assert np.allclose(
        results["net_return"],
        expected_net_return,
        atol=1e-10,
    )