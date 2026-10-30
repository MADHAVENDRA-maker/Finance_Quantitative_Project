from collections.abc import Mapping

import numpy as np
import pandas as pd


def validate_portfolio_weights(
    weights: pd.Series | Mapping[str, float],
) -> pd.Series:
    """Validate portfolio weights and return them as a pandas Series."""
    if isinstance(weights, Mapping):
        weights = pd.Series(dict(weights), dtype=float)
    elif isinstance(weights, pd.Series):
        weights = weights.copy()
    else:
        raise TypeError("Weights must be a pandas Series or mapping.")

    if weights.empty:
        raise ValueError("Portfolio weights must not be empty.")

    if weights.index.has_duplicates:
        raise ValueError("Portfolio weights contain duplicate asset names.")

    if not all(isinstance(asset, str) and asset.strip() for asset in weights.index):
        raise ValueError("Asset names must be non-empty strings.")

    try:
        values = weights.to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Portfolio weights must be numeric.") from exc

    if not np.isfinite(values).all():
        raise ValueError("Portfolio weights must be finite.")

    if not np.isclose(values.sum(), 1.0, rtol=0.0, atol=1e-8):
        raise ValueError("Portfolio weights must sum to 1.")

    weights = pd.Series(values, index=weights.index, dtype=float)
    weights.index.name = "ticker"
    return weights


def calculate_portfolio_returns(
    asset_returns: pd.DataFrame,
    weights: pd.Series | Mapping[str, float],
) -> pd.Series:
    """Calculate periodic portfolio returns from asset simple returns.

    Assumes the portfolio is rebalanced to the specified weights at the
    beginning of each return period.
    """
    if not isinstance(asset_returns, pd.DataFrame):
        raise TypeError("Asset returns must be supplied as a pandas DataFrame.")

    if asset_returns.empty or asset_returns.shape[1] == 0:
        raise ValueError("Asset returns must contain assets and observations.")

    if asset_returns.columns.has_duplicates:
        raise ValueError("Asset returns contain duplicate asset columns.")

    validated_weights = validate_portfolio_weights(weights)

    if set(asset_returns.columns) != set(validated_weights.index):
        raise ValueError(
            "Asset return columns must match the assets in portfolio weights."
        )

    if asset_returns.isna().any().any():
        raise ValueError("Asset returns contain missing observations.")

    try:
        values = asset_returns.to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Asset returns must be numeric.") from exc

    if not np.isfinite(values).all():
        raise ValueError("Asset returns contain non-finite values.")

    aligned_returns = asset_returns.loc[:, validated_weights.index].astype(float)
    portfolio_returns = aligned_returns @ validated_weights
    portfolio_returns.name = "portfolio_return"

    return portfolio_returns


def calculate_portfolio_volatility(
    covariance: pd.DataFrame,
    weights: pd.Series | Mapping[str, float],
    periods_per_year: int = 252,
) -> float:
    """Calculate annualized portfolio volatility from a covariance matrix.

    The covariance matrix must represent periodic return covariance.
    For daily covariance, the default annualization factor is 252.
    """
    if not isinstance(covariance, pd.DataFrame):
        raise TypeError("Covariance must be supplied as a pandas DataFrame.")

    if covariance.empty or covariance.shape[0] != covariance.shape[1]:
        raise ValueError("Covariance must be a non-empty square matrix.")

    if covariance.index.has_duplicates or covariance.columns.has_duplicates:
        raise ValueError("Covariance matrix labels must be unique.")

    if list(covariance.index) != list(covariance.columns):
        raise ValueError("Covariance row and column labels must match.")

    if (
        not isinstance(periods_per_year, int)
        or isinstance(periods_per_year, bool)
        or periods_per_year <= 0
    ):
        raise ValueError("periods_per_year must be a positive integer.")

    validated_weights = validate_portfolio_weights(weights)

    if set(covariance.index) != set(validated_weights.index):
        raise ValueError(
            "Covariance matrix assets must match the portfolio weight assets."
        )

    try:
        matrix = covariance.loc[
            validated_weights.index, validated_weights.index
        ].to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Covariance matrix must contain numeric values.") from exc

    if not np.isfinite(matrix).all():
        raise ValueError("Covariance matrix contains non-finite values.")

    if not np.allclose(matrix, matrix.T, rtol=1e-7, atol=1e-12):
        raise ValueError("Covariance matrix must be symmetric.")

    weight_values = validated_weights.to_numpy(dtype=float)
    variance = float(weight_values @ matrix @ weight_values)

    if variance < -1e-12:
        raise ValueError("Portfolio variance is negative.")

    variance = max(variance, 0.0)
    annualized_volatility = np.sqrt(variance * periods_per_year)

    return float(annualized_volatility)