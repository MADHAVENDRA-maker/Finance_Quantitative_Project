from collections.abc import Mapping

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from project_structure.portfolio.optimization import _validate_covariance_matrix


def calculate_maximum_sharpe_weights(
    expected_returns: pd.Series | Mapping[str, float],
    covariance: pd.DataFrame,
    risk_free_rate: float = 0.0,
) -> pd.Series:
    """Find long-only weights maximizing estimated Sharpe ratio.

    Expected returns, covariance, and risk_free_rate must all use the
    same periodic frequency.
    """
    if isinstance(expected_returns, Mapping):
        expected_returns = pd.Series(dict(expected_returns), dtype=float)
    elif isinstance(expected_returns, pd.Series):
        expected_returns = expected_returns.copy()
    else:
        raise TypeError(
            "Expected returns must be a pandas Series or mapping."
        )

    if expected_returns.empty:
        raise ValueError("Expected returns must not be empty.")

    if expected_returns.index.has_duplicates:
        raise ValueError("Expected-return asset names must be unique.")

    if not all(
        isinstance(asset, str) and asset.strip()
        for asset in expected_returns.index
    ):
        raise ValueError("Expected-return asset names must be non-empty strings.")

    try:
        mu = expected_returns.to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Expected returns must be numeric.") from exc

    if not np.isfinite(mu).all():
        raise ValueError("Expected returns must be finite.")

    if (
        isinstance(risk_free_rate, bool)
        or not isinstance(risk_free_rate, (int, float, np.integer, np.floating))
        or not np.isfinite(risk_free_rate)
    ):
        raise ValueError("Risk-free rate must be a finite number.")

    covariance = _validate_covariance_matrix(covariance)
    assets = list(covariance.columns)

    if set(expected_returns.index) != set(assets):
        raise ValueError(
            "Expected-return assets must match covariance matrix assets."
        )

    mu = expected_returns.loc[assets].to_numpy(dtype=float)
    matrix = covariance.to_numpy(dtype=float)
    excess_returns = mu - float(risk_free_rate)

    if np.max(np.abs(matrix)) <= 1e-15:
        raise ValueError(
            "Cannot optimize the Sharpe ratio with zero covariance."
        )

    n_assets = len(assets)

    def negative_sharpe(weights: np.ndarray) -> float:
        variance = float(weights @ matrix @ weights)

        if not np.isfinite(variance) or variance <= 1e-16:
            return 1e12

        excess_return = float(weights @ excess_returns)
        return -excess_return / np.sqrt(variance)

    constraints = [
        {
            "type": "eq",
            "fun": lambda weights: float(np.sum(weights) - 1.0),
        }
    ]
    bounds = [(0.0, 1.0)] * n_assets

    # Try equal weights and every single-asset allocation.
    starts = [np.full(n_assets, 1.0 / n_assets)]
    starts.extend(np.eye(n_assets))

    candidates = []

    for initial_weights in starts:
        result = minimize(
            negative_sharpe,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 2000, "ftol": 1e-12},
        )

        if result.success and np.isfinite(result.x).all():
            weights = np.asarray(result.x, dtype=float)

            if (
                np.all(weights >= -1e-7)
                and np.all(weights <= 1.0 + 1e-7)
                and np.isclose(weights.sum(), 1.0, atol=1e-7)
            ):
                weights = np.clip(weights, 0.0, 1.0)
                weights /= weights.sum()
                candidates.append((negative_sharpe(weights), weights))

    if not candidates:
        raise RuntimeError(
            "Maximum-Sharpe optimization failed from all starting points."
        )

    _, weights = min(candidates, key=lambda candidate: candidate[0])

    if float(weights @ matrix @ weights) <= 1e-16:
        raise RuntimeError("Optimizer returned a zero-volatility portfolio.")

    return pd.Series(
        weights,
        index=pd.Index(assets, name="ticker"),
        dtype=float,
        name="weight",
    )