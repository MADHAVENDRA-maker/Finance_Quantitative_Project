from pathlib import Path

import pandas as pd
import pytest

from project_structure.data import downloader


def sample_history() -> pd.DataFrame:
    """Create sample price data without accessing an external API."""

    dates = pd.to_datetime(["2025-01-02", "2025-01-03"])

    return pd.DataFrame(
        {
            "Open": [590.0, 592.0],
            "High": [595.0, 596.0],
            "Low": [589.0, 591.0],
            "Close": [593.0, 594.0],
            "Volume": [1_000_000, 1_200_000],
        },
        index=pd.DatetimeIndex(dates, name="Date"),
    )


def test_download_asset_history_returns_data(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTicker:
        def __init__(self, ticker: str) -> None:
            assert ticker == "SPY"

        def history(self, **kwargs: object) -> pd.DataFrame:
            assert kwargs["start"] == "2025-01-01"
            assert kwargs["end"] == "2025-02-01"
            return sample_history()

    monkeypatch.setattr(downloader.yf, "Ticker", FakeTicker)

    result = downloader.download_asset_history(
        ticker=" spy ",
        start="2025-01-01",
        end="2025-02-01",
    )

    assert len(result) == 2
    assert result.index.name == "Date"
    assert "Close" in result.columns


def test_empty_download_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTicker:
        def __init__(self, ticker: str) -> None:
            pass

        def history(self, **kwargs: object) -> pd.DataFrame:
            return pd.DataFrame()

    monkeypatch.setattr(downloader.yf, "Ticker", FakeTicker)

    with pytest.raises(ValueError, match="No historical data"):
        downloader.download_asset_history(
            ticker="SPY",
            start="2025-01-01",
            end="2025-02-01",
        )


def test_api_failure_is_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTicker:
        def __init__(self, ticker: str) -> None:
            pass

        def history(self, **kwargs: object) -> pd.DataFrame:
            raise OSError("Simulated network failure")

    monkeypatch.setattr(downloader.yf, "Ticker", FakeTicker)

    with pytest.raises(RuntimeError, match="Failed to download") as exc_info:
        downloader.download_asset_history(
            ticker="SPY",
            start="2025-01-01",
            end="2025-02-01",
        )

    assert isinstance(exc_info.value.__cause__, OSError)


def test_download_universe_saves_csv_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_download(
        ticker: str,
        start: str,
        end: str | None = None,
    ) -> pd.DataFrame:
        return sample_history()

    monkeypatch.setattr(downloader, "download_asset_history", fake_download)

    result = downloader.download_universe(
        tickers=["SPY", "TLT"],
        start="2025-01-01",
        end="2025-02-01",
        output_dir=tmp_path,
    )

    assert set(result) == {"SPY", "TLT"}

    for ticker in ["SPY", "TLT"]:
        csv_path = tmp_path / f"{ticker}.csv"
        assert csv_path.is_file()

        saved_data = pd.read_csv(csv_path)
        assert len(saved_data) == 2
        assert "Date" in saved_data.columns
        assert "Close" in saved_data.columns


def test_empty_ticker_list_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least one ticker"):
        downloader.download_universe(
            tickers=[],
            output_dir=tmp_path,
        )


def test_duplicate_tickers_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Duplicate ticker"):
        downloader.download_universe(
            tickers=["SPY", "spy"],
            output_dir=tmp_path,
        )


def test_invalid_date_range_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="start"):
        downloader.download_universe(
            tickers=["SPY"],
            start="2025-02-01",
            end="2025-01-01",
            output_dir=tmp_path,
        )