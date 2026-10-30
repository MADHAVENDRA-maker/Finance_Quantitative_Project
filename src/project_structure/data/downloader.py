from collections.abc import Sequence
from datetime import date
from pathlib import Path

import pandas as pd
import yfinance as yf

from project_structure.config import PROJECT_ROOT, load_assets_config

DEFAULT_RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def download_asset_history(
    ticker: str,
    start: str | date,
    end: str | date | None = None,
) -> pd.DataFrame:
    """Download daily historical price data for one ETF."""

    normalized_ticker = ticker.strip().upper()

    if not normalized_ticker:
        raise ValueError("Ticker must not be empty.")

    if end is not None and str(start) >= str(end):
        raise ValueError("'start' must be earlier than 'end'.")

    try:
        history = yf.Ticker(normalized_ticker).history(
            start=str(start),
            end=str(end) if end is not None else None,
            interval="1d",
            auto_adjust=False,
            actions=False,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download historical data for {normalized_ticker}."
        ) from exc

    if history.empty:
        raise ValueError(
            f"No historical data returned for {normalized_ticker}. "
            "Check the ticker, date range, and network connection."
        )

    history.index.name = "Date"
    return history


def download_universe(
    tickers: Sequence[str] | None = None,
    start: str | date = "2020-01-01",
    end: str | date | None = None,
    output_dir: str | Path = DEFAULT_RAW_DATA_DIR,
) -> dict[str, pd.DataFrame]:
    """Download and save daily history for the selected configured ETFs."""

    if tickers is None:
        config = load_assets_config()
        selected_tickers = [asset.ticker for asset in config.assets]
    else:
        selected_tickers = [ticker.strip().upper() for ticker in tickers]

    if not selected_tickers:
        raise ValueError("Select at least one ticker.")

    if any(not ticker for ticker in selected_tickers):
        raise ValueError("Ticker symbols must not be empty.")

    if len(selected_tickers) != len(set(selected_tickers)):
        raise ValueError("Duplicate ticker symbols are not allowed.")

    if end is not None and str(start) >= str(end):
        raise ValueError("'start' must be earlier than 'end'.")

    output_path = Path(output_dir)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    # Download everything before writing files, so a failed download
    # does not leave a newly downloaded partial universe on disk.
    downloaded: dict[str, pd.DataFrame] = {}

    for ticker in selected_tickers:
        downloaded[ticker] = download_asset_history(
            ticker=ticker,
            start=start,
            end=end,
        )

    output_path.mkdir(parents=True, exist_ok=True)

    for ticker, history in downloaded.items():
        file_path = output_path / f"{ticker}.csv"
        history.to_csv(file_path, index=True, index_label="Date")

    return downloaded