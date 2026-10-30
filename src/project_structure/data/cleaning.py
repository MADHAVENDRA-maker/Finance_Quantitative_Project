import numpy as np
import pandas as pd

REQUIRED_PRICE_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


def clean_price_history(history: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean historical OHLCV market data.

    - Accepts a Date column or a date-based index.
    - Sorts observations chronologically.
    - Rejects duplicate dates and invalid prices.
    - Removes rows with missing required OHLCV values.
    - Preserves additional columns, such as Adjusted Close.
    """

    if not isinstance(history, pd.DataFrame):
        raise TypeError("Historical data must be a pandas DataFrame.")

    if history.empty:
        raise ValueError("Historical data must not be empty.")

    data = history.copy()

    # Standardize the date index.
    if "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"], errors="raise")
        data = data.set_index("Date")
    else:
        data.index = pd.to_datetime(data.index, errors="raise")

    data.index.name = "Date"

    if data.index.hasnans:
        raise ValueError("Historical data contains invalid dates.")

    if data.index.has_duplicates:
        raise ValueError("Historical data contains duplicate dates.")

    # Confirm that all required OHLCV fields are available.
    missing_columns = [
        column for column in REQUIRED_PRICE_COLUMNS if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Historical data is missing required columns: {missing_columns}"
        )

    # Convert required fields to numeric values.
    for column in REQUIRED_PRICE_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="raise")

    # Remove observations that cannot be used for OHLCV calculations.
    data = data.dropna(subset=list(REQUIRED_PRICE_COLUMNS))

    if data.empty:
        raise ValueError("No valid observations remain after removing missing values.")

    # Reject infinite values and invalid prices.
    values = data.loc[:, REQUIRED_PRICE_COLUMNS].to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise ValueError("Historical data contains infinite or invalid OHLCV values.")

    price_columns = ("Open", "High", "Low", "Close")

    if (data.loc[:, price_columns] <= 0).any().any():
        raise ValueError("OHLC prices must be strictly positive.")

    if (data["Volume"] < 0).any():
        raise ValueError("Volume must not be negative.")

    # Validate the internal consistency of daily OHLC prices.
    invalid_ohlc = (
        (data["High"] < data["Low"])
        | (data["High"] < data[["Open", "Close"]].max(axis=1))
        | (data["Low"] > data[["Open", "Close"]].min(axis=1))
    )

    if invalid_ohlc.any():
        raise ValueError("Historical data contains inconsistent OHLC prices.")

    # Return observations in chronological order.
    return data.sort_index()