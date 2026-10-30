import numpy as np
import pandas as pd

"""Correlation and covariance analysis for asset returns."""

def _validate_returns(returns: pd.DataFrame) -> pd.DataFrame:
    """Validate a complete returns DataFrame for relationship analysis."""
    if not isinstance(returns, pd.DataFrame):
        raise TypeError("Returns must be supplied as a pandas DataFrame.")

    if returns.empty or returns.shape[1] < 1:
        raise ValueError("Returns must contain at least one asset and one row.")

    if returns.columns.has_duplicates:
        raise ValueError("Returns contain duplicate asset columns.")

    if returns.isna().any().any():
        raise ValueError("Returns contain missing observations.")

    try:
        values = returns.to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Returns must contain only numeric values.") from exc

    if not np.isfinite(values).all():
        raise ValueError("Returns contain infinite or invalid values.")

    if len(returns) < 2:
        raise ValueError("At least two observations are required.")

    if (returns.std(ddof=1) == 0).any():
        raise ValueError("Returns contain an asset with zero variance.")

    return returns.astype(float)


def calculate_correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """Calculate pairwise Pearson correlations between asset returns."""
    validated = _validate_returns(returns)
    return validated.corr(method="pearson")


def calculate_covariance_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """Calculate the sample covariance matrix of asset returns."""
    validated = _validate_returns(returns)
    return validated.cov(ddof=1)


def calculate_rolling_correlation(
    returns: pd.DataFrame,
    asset_1: str,
    asset_2: str,
    window: int = 60,
) -> pd.Series:
    """Calculate rolling correlation between two assets.

    The window is measured in observations, not calendar days.
    """
    if not isinstance(window, int) or isinstance(window, bool) or window < 2:
        raise ValueError("window must be an integer greater than or equal to 2.")

    if not isinstance(returns, pd.DataFrame):
        raise TypeError("Returns must be supplied as a pandas DataFrame.")

    if asset_1 == asset_2:
        raise ValueError("The two assets must be different.")

    if asset_1 not in returns.columns or asset_2 not in returns.columns:
        raise ValueError("Both assets must exist in the returns DataFrame.")

    if len(returns) < window:
        raise ValueError("The number of observations must be at least window.")

    validated = _validate_returns(returns)

    result = validated[asset_1].rolling(window=window).corr(
        validated[asset_2]
    )
    result.name = f"{asset_1}_{asset_2}_rolling_correlation"
    return result