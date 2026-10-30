from pathlib import Path

import pandas as pd
import pytest

from project_structure.data import pipeline


def sample_history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [100.0, 102.0],
            "High": [105.0, 106.0],
            "Low": [99.0, 101.0],
            "Close": [103.0, 104.0],
            "Volume": [1000, 1200],
        },
        index=pd.to_datetime(["2025-01-02", "2025-01-03"]),
    )


def test_pipeline_saves_cleaned_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_download(**kwargs: object) -> dict[str, pd.DataFrame]:
        return {"SPY": sample_history(), "TLT": sample_history()}

    monkeypatch.setattr(pipeline, "download_universe", fake_download)

    output_dir = tmp_path / "processed"

    result = pipeline.run_data_pipeline(
        tickers=["SPY", "TLT"],
        processed_output_dir=output_dir,
    )

    assert set(result) == {"SPY", "TLT"}

    for ticker in ["SPY", "TLT"]:
        file_path = output_dir / f"{ticker}.csv"
        assert file_path.is_file()

        saved = pd.read_csv(file_path)
        assert len(saved) == 2
        assert "Date" in saved.columns
        assert "Close" in saved.columns


def test_pipeline_does_not_write_files_if_validation_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    invalid_history = sample_history()
    invalid_history.iloc[0, invalid_history.columns.get_loc("Close")] = 0.0

    def fake_download(**kwargs: object) -> dict[str, pd.DataFrame]:
        return {
            "SPY": sample_history(),
            "TLT": invalid_history,
        }

    monkeypatch.setattr(pipeline, "download_universe", fake_download)

    output_dir = tmp_path / "processed"

    with pytest.raises(ValueError, match="strictly positive"):
        pipeline.run_data_pipeline(
            tickers=["SPY", "TLT"],
            processed_output_dir=output_dir,
        )

    assert not output_dir.exists()