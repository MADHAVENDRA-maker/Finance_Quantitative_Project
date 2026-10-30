import pandas as pd
from collections.abc import Mapping
from project_structure.features.relationships import calculate_covariance_matrix
from project_structure.portfolio.max_sharpe import calculate_maximum_sharpe_weights
from project_structure.portfolio.optimization import (
    calculate_equal_weights,
    calculate_minimum_variance_weights,
)
from project_structure.portfolio.analytics import validate_portfolio_weights


def equal_weight_strategy(history: pd.DataFrame) -> pd.Series:
    """Allocate equally across all assets in the supplied history."""
    if history.empty:
        raise ValueError("Historical returns cannot be empty.")

    return calculate_equal_weights(list(history.columns))


def minimum_variance_strategy(history: pd.DataFrame) -> pd.Series:
    """Calculate minimum-variance weights from historical returns only."""
    if history.empty:
        raise ValueError("Historical returns cannot be empty.")

    covariance = calculate_covariance_matrix(history)
    return calculate_minimum_variance_weights(covariance)


def maximum_sharpe_strategy(
    history: pd.DataFrame,
    risk_free_rate: float = 0.0,
) -> pd.Series:
    """Calculate maximum-Sharpe weights from historical returns only.

    The risk-free rate must use the same periodic frequency as the returns.
    For daily returns, supply a daily risk-free rate.
    """
    if history.empty:
        raise ValueError("Historical returns cannot be empty.")

    expected_returns = history.mean()
    covariance = calculate_covariance_matrix(history)

    return calculate_maximum_sharpe_weights(
        expected_returns=expected_returns,
        covariance=covariance,
        risk_free_rate=risk_free_rate,
    )


def custom_weight_strategy(
    weights: pd.Series | Mapping[str, float],
):
    """Create a strategy that rebalances to fixed user-defined weights.

    Parameters
    ----------
    weights:
        Mapping of ETF tickers to long-only portfolio weights.
        Weights must sum to 1.

    Returns
    -------
    Callable
        A strategy compatible with run_backtest. It returns the same
        target weights at every scheduled rebalance.
    """
    target_weights = validate_portfolio_weights(weights)

    if (target_weights < 0).any() or (target_weights > 1).any():
        raise ValueError(
            "Custom portfolio weights must be between 0 and 1."
        )

    target_weights = target_weights.copy()

    def strategy(history: pd.DataFrame) -> pd.Series:
        if history.empty:
            raise ValueError("Historical returns cannot be empty.")

        if set(history.columns) != set(target_weights.index):
            raise ValueError(
                "Selected ETF columns must match the custom portfolio weights."
            )

        return target_weights.reindex(history.columns).copy()

    return strategy