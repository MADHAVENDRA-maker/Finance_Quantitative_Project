import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def _validate_returns(
    net_returns: pd.Series,
    window: int,
) -> None:
    """Validate net returns and the rolling window."""
    if not isinstance(net_returns, pd.Series):
        raise TypeError("net_returns must be a pandas Series.")

    if net_returns.empty:
        raise ValueError("net_returns cannot be empty.")

    if not isinstance(window, (int, np.integer)) or isinstance(
        window, (bool, np.bool_)
    ):
        raise TypeError("window must be an integer.")

    if window < 2:
        raise ValueError("window must be at least 2.")

    if not pd.api.types.is_numeric_dtype(net_returns.dtype):
        raise TypeError("net_returns must contain numeric values.")

    values = net_returns.to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise ValueError("net_returns must contain only finite values.")

    if (values < -1.0).any():
        raise ValueError("net_returns cannot be below -100%.")


def calculate_rolling_sharpe(
    net_returns: pd.Series,
    window: int = 63,
    risk_free_rate: float = 0.0,
) -> pd.Series:
    """Calculate annualized rolling Sharpe ratios.

    risk_free_rate is the annual risk-free rate expressed as a decimal.
    """
    _validate_returns(net_returns, window)

    if isinstance(risk_free_rate, (bool, np.bool_)) or not isinstance(
        risk_free_rate, (int, float, np.integer, np.floating)
    ):
        raise TypeError("risk_free_rate must be numeric.")

    if not np.isfinite(risk_free_rate):
        raise ValueError("risk_free_rate must be finite.")

    daily_risk_free_rate = (1.0 + risk_free_rate) ** (
        1.0 / TRADING_DAYS_PER_YEAR
    ) - 1.0

    excess_returns = net_returns.astype(float) - daily_risk_free_rate

    rolling_mean = excess_returns.rolling(
        window=window,
        min_periods=window,
    ).mean()

    rolling_std = excess_returns.rolling(
        window=window,
        min_periods=window,
    ).std(ddof=1)

    rolling_sharpe = (
        np.sqrt(TRADING_DAYS_PER_YEAR) * rolling_mean / rolling_std
    )

    return rolling_sharpe.replace([np.inf, -np.inf], np.nan).rename(
        "rolling_sharpe"
    )


def calculate_rolling_volatility(
    net_returns: pd.Series,
    window: int = 63,
) -> pd.Series:
    """Calculate annualized rolling volatility of net returns."""
    _validate_returns(net_returns, window)

    rolling_volatility = (
        net_returns.astype(float)
        .rolling(window=window, min_periods=window)
        .std(ddof=1)
        * np.sqrt(TRADING_DAYS_PER_YEAR)
    )

    return rolling_volatility.rename("rolling_volatility")