from collections.abc import Sequence
from datetime import date
from pathlib import Path

import pandas as pd

from project_structure.config import PROJECT_ROOT
from project_structure.data.cleaning import clean_price_history
from project_structure.data.downloader import download_universe

DEFAULT_PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def run_data_pipeline(
    tickers: Sequence[str] | None = None,
    start: str | date = "2020-01-01",
    end: str | date | None = None,
    raw_output_dir: str | Path | None = None,
    processed_output_dir: str | Path = DEFAULT_PROCESSED_DATA_DIR,
) -> dict[str, pd.DataFrame]:
    """Download, validate, clean, and save historical ETF price data.

    Raw CSV files are managed by the downloader. Processed CSV files
    are written only after all downloaded datasets pass validation.
    """

    download_kwargs: dict[str, object] = {
        "tickers": tickers,
        "start": start,
        "end": end,
    }

    if raw_output_dir is not None:
        download_kwargs["output_dir"] = raw_output_dir

    raw_data = download_universe(**download_kwargs)

    # Validate every dataset before writing any processed files.
    cleaned_data = {
        ticker: clean_price_history(history)
        for ticker, history in raw_data.items()
    }

    output_path = Path(processed_output_dir)

    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    output_path.mkdir(parents=True, exist_ok=True)

    for ticker, history in cleaned_data.items():
        file_path = output_path / f"{ticker}.csv"
        history.to_csv(file_path, index=True, index_label="Date")

    return cleaned_data