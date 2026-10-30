from collections.abc import Mapping

import numpy as np
import pandas as pd


def calculate_asset_returns(
    history: pd.DataFrame,
    price_column: str | None = None,
) -> pd.DataFrame:
    """Calculate daily simple and logarithmic returns for one asset.

    Adjusted Close is preferred when available because it accounts for
    distributions and splits reflected in the adjusted price series.
    Close is used as a fallback.

    The first return is NaN because no previous observation exists.
    """

    if not isinstance(history, pd.DataFrame):
        raise TypeError("Historical data must be a pandas DataFrame.")

    if history.empty:
        raise ValueError("Historical data must not be empty.")

    if price_column is None:
        if "Adj Close" in history.columns:
            price_column = "Adj Close"
        elif "Close" in history.columns:
            price_column = "Close"
        else:
            raise ValueError(
                "Historical data must contain 'Adj Close' or 'Close'."
            )

    if price_column not in history.columns:
        raise ValueError(f"Price column '{price_column}' was not found.")

    prices = pd.to_numeric(history[price_column], errors="raise")

    if prices.isna().any():
        raise ValueError("Price series contains missing values.")

    values = prices.to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise ValueError("Price series contains infinite or invalid values.")

    if (prices <= 0).any():
        raise ValueError("Prices must be strictly positive.")

    simple_returns = prices.pct_change(fill_method=None)
    log_returns = np.log(prices / prices.shift(1))

    return pd.DataFrame(
        {
            "simple_return": simple_returns,
            "log_return": log_returns,
        },
        index=history.index.copy(),
    )


def calculate_universe_returns(
    histories: Mapping[str, pd.DataFrame],
    return_type: str = "simple",
    price_column: str | None = None,
) -> pd.DataFrame:
    """Calculate aligned daily returns for multiple assets.

    Returns a wide DataFrame with one column per ticker and dates as
    the index. Dates absent from an asset's history remain NaN.
    """

    if not histories:
        raise ValueError("At least one asset history is required.")

    if return_type not in {"simple", "log"}:
        raise ValueError("return_type must be either 'simple' or 'log'.")

    tickers = list(histories)

    if any(not ticker.strip() for ticker in tickers):
        raise ValueError("Ticker symbols must not be empty.")

    if len({ticker.upper() for ticker in tickers}) != len(tickers):
        raise ValueError("Duplicate ticker symbols are not allowed.")

    return_column = (
        "simple_return" if return_type == "simple" else "log_return"
    )

    return_series: dict[str, pd.Series] = {}

    for ticker, history in histories.items():
        asset_returns = calculate_asset_returns(
            history,
            price_column=price_column,
        )
        return_series[ticker.upper()] = asset_returns[return_column]

    return pd.DataFrame(return_series).sort_index()