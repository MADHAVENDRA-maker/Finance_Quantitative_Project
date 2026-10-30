from collections.abc import Callable

import numpy as np
import pandas as pd

Strategy = Callable[[pd.DataFrame], pd.Series]


def _validate_asset_returns(asset_returns: pd.DataFrame) -> None:
    """Validate a dated DataFrame of asset returns."""
    if not isinstance(asset_returns, pd.DataFrame):
        raise TypeError("asset_returns must be a pandas DataFrame.")

    if asset_returns.empty:
        raise ValueError("asset_returns cannot be empty.")

    if asset_returns.shape[1] == 0:
        raise ValueError("At least one asset is required.")

    if not asset_returns.columns.is_unique:
        raise ValueError("Asset columns must be unique.")

    if not asset_returns.index.is_unique:
        raise ValueError("Return dates must be unique.")

    if not asset_returns.index.is_monotonic_increasing:
        raise ValueError("Return dates must be sorted in ascending order.")

    if asset_returns.isna().any().any():
        raise ValueError("Asset returns cannot contain missing values.")

    values = asset_returns.to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise ValueError("Asset returns must contain only finite values.")

    if (values < -1.0).any():
        raise ValueError("Asset returns cannot be below -100%.")


def _validate_target_weights(
    weights: pd.Series,
    asset_names: pd.Index,
) -> pd.Series:
    """Validate and align a strategy's target portfolio weights."""
    if not isinstance(weights, pd.Series):
        raise TypeError("A strategy must return a pandas Series of weights.")

    if not weights.index.is_unique:
        raise ValueError("Weight labels must be unique.")

    if set(weights.index) != set(asset_names):
        raise ValueError("Weight labels must match the asset return columns.")

    weights = weights.reindex(asset_names).astype(float)

    if not np.isfinite(weights.to_numpy()).all():
        raise ValueError("Portfolio weights must be finite.")

    if (weights < -1e-8).any() or (weights > 1.0 + 1e-8).any():
        raise ValueError("Weights must be long-only and between 0 and 1.")

    if not np.isclose(weights.sum(), 1.0, atol=1e-6):
        raise ValueError("Portfolio weights must sum to 1.")

    weights = weights.clip(lower=0.0, upper=1.0)
    return weights / weights.sum()


def run_backtest(
    asset_returns: pd.DataFrame,
    strategy: Strategy,
    lookback: int = 252,
    rebalance_every: int = 21,
    transaction_cost_bps: float = 10.0,
) -> pd.DataFrame:
    """Backtest a long-only strategy with drift and transaction costs.

    The strategy uses only trailing returns available before each evaluated
    return. Portfolio weights drift as asset prices change between rebalances.
    Turnover is measured against the portfolio's drifted pre-trade weights.

    Transaction costs are charged at the start of the period in which
    rebalancing occurs. Initial portfolio establishment incurs turnover of 1.

    Returns
    -------
    pandas.DataFrame
        Out-of-sample gross and net returns, turnover, transaction costs,
        and the weights applied at the start of each period.
    """
    _validate_asset_returns(asset_returns)

    if not callable(strategy):
        raise TypeError("strategy must be a callable function.")

    if isinstance(lookback, bool) or not isinstance(lookback, int):
        raise TypeError("lookback must be an integer.")

    if isinstance(rebalance_every, bool) or not isinstance(
        rebalance_every, int
    ):
        raise TypeError("rebalance_every must be an integer.")

    if lookback < 2:
        raise ValueError("lookback must be at least 2.")

    if rebalance_every < 1:
        raise ValueError("rebalance_every must be at least 1.")

    if isinstance(transaction_cost_bps, (bool, np.bool_)) or not isinstance(
        transaction_cost_bps, (int, float, np.integer, np.floating)
    ):
        raise TypeError("transaction_cost_bps must be a numeric value.")

    if not np.isfinite(transaction_cost_bps) or transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps must be finite and non-negative.")

    if len(asset_returns) <= lookback:
        raise ValueError(
            "Need more observations than lookback to generate "
            "out-of-sample returns."
        )

    asset_names = asset_returns.columns
    cost_rate = transaction_cost_bps / 10_000.0

    records = []
    actual_weights = None

    for i in range(lookback, len(asset_returns)):
        is_rebalance = (
            actual_weights is None
            or (i - lookback) % rebalance_every == 0
        )

        turnover = 0.0
        transaction_cost = 0.0

        if is_rebalance:
            training_returns = asset_returns.iloc[i - lookback : i].copy()
            target_weights = _validate_target_weights(
                strategy(training_returns),
                asset_names,
            )

            if actual_weights is None:
                # Establish the initial portfolio from cash.
                turnover = 1.0
            else:
                # Trade from the actual drifted holdings to target weights.
                turnover = float(
                    (target_weights - actual_weights).abs().sum()
                )

            transaction_cost = cost_rate * turnover
            actual_weights = target_weights.copy()

        # These are the weights held at the start of this period.
        applied_weights = actual_weights.copy()
        period_returns = asset_returns.iloc[i]
        gross_return = float(period_returns.dot(applied_weights))

        # A total loss makes subsequent portfolio weights undefined.
        if gross_return <= -1.0:
            raise ValueError(
                "The portfolio lost all its value; subsequent weights "
                "cannot be calculated."
            )

        # Deduct trading costs at the start of the period.
        net_return = (1.0 - transaction_cost) * (1.0 + gross_return) - 1.0

        record = {
            "gross_return": gross_return,
            "net_return": net_return,
            "turnover": turnover,
            "transaction_cost": transaction_cost,
        }

        for asset in asset_names:
            record[f"weight_{asset}"] = float(applied_weights[asset])

        records.append(record)

        # Let holdings drift with each asset's return until the next rebalance.
        asset_growth = 1.0 + period_returns
        portfolio_growth = 1.0 + gross_return

        actual_weights = applied_weights * asset_growth / portfolio_growth
        actual_weights = actual_weights / actual_weights.sum()

    results = pd.DataFrame(
        records,
        index=asset_returns.index[lookback:],
    )
    results.index.name = asset_returns.index.name or "Date"

    return results