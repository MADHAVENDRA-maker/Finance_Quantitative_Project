import pandas as pd
import pytest

from project_structure.data.cleaning import clean_price_history


def sample_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [100.0, 102.0, 103.0],
            "High": [105.0, 106.0, 107.0],
            "Low": [99.0, 101.0, 102.0],
            "Close": [103.0, 104.0, 106.0],
            "Volume": [1000, 1200, 1100],
            "Adj Close": [103.0, 104.0, 106.0],
        },
        index=pd.to_datetime(
            ["2025-01-03", "2025-01-02", "2025-01-06"]
        ),
    )


def test_data_is_sorted_chronologically() -> None:
    result = clean_price_history(sample_prices())

    assert result.index.is_monotonic_increasing
    assert result.index.name == "Date"


def test_missing_required_values_are_removed() -> None:
    data = sample_prices()
    data.iloc[0, data.columns.get_loc("Close")] = float("nan")

    result = clean_price_history(data)

    assert len(result) == 2
    assert result["Close"].notna().all()


def test_duplicate_dates_are_rejected() -> None:
    data = sample_prices()
    data.index = pd.to_datetime(
        ["2025-01-03", "2025-01-03", "2025-01-06"]
    )

    with pytest.raises(ValueError, match="duplicate dates"):
        clean_price_history(data)


def test_nonpositive_prices_are_rejected() -> None:
    data = sample_prices()
    data.iloc[0, data.columns.get_loc("Close")] = 0.0

    with pytest.raises(ValueError, match="strictly positive"):
        clean_price_history(data)


def test_inconsistent_ohlc_prices_are_rejected() -> None:
    data = sample_prices()
    data.iloc[0, data.columns.get_loc("High")] = 98.0

    with pytest.raises(ValueError, match="inconsistent OHLC"):
        clean_price_history(data)


def test_missing_required_column_is_rejected() -> None:
    data = sample_prices().drop(columns=["Volume"])

    with pytest.raises(ValueError, match="missing required columns"):
        clean_price_history(data)


def test_date_column_is_supported() -> None:
    data = sample_prices().reset_index()
    data = data.rename(columns={"index": "Date"})

    result = clean_price_history(data)

    assert result.index.name == "Date"
    assert result.index.is_monotonic_increasing


def test_empty_data_is_rejected() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        clean_price_history(pd.DataFrame())