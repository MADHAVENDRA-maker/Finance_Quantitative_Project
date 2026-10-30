import numpy as np
import pandas as pd
import pytest

from project_structure.data.returns import calculate_asset_returns, calculate_universe_returns


def sample_history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Close": [100.0, 110.0, 99.0],
            "Adj Close": [100.0, 110.0, 99.0],
        },
        index=pd.to_datetime(
            ["2025-01-02", "2025-01-03", "2025-01-06"]
        ),
    )


def test_simple_returns_are_calculated_correctly() -> None:
    result = calculate_asset_returns(sample_history())

    assert pd.isna(result["simple_return"].iloc[0])
    assert result["simple_return"].iloc[1] == pytest.approx(0.10)
    assert result["simple_return"].iloc[2] == pytest.approx(-0.10)


def test_log_returns_are_calculated_correctly() -> None:
    result = calculate_asset_returns(sample_history())

    assert result["log_return"].iloc[1] == pytest.approx(np.log(1.10))
    assert result["log_return"].iloc[2] == pytest.approx(np.log(0.90))


def test_adjusted_close_is_preferred() -> None:
    history = pd.DataFrame(
        {"Close": [100.0, 120.0], "Adj Close": [100.0, 110.0]}
    )

    result = calculate_asset_returns(history)

    assert result["simple_return"].iloc[1] == pytest.approx(0.10)


def test_close_is_used_when_adjusted_close_is_absent() -> None:
    history = pd.DataFrame({"Close": [100.0, 105.0]})

    result = calculate_asset_returns(history)

    assert result["simple_return"].iloc[1] == pytest.approx(0.05)


def test_missing_prices_are_rejected() -> None:
    history = pd.DataFrame({"Close": [100.0, np.nan]})

    with pytest.raises(ValueError, match="missing values"):
        calculate_asset_returns(history)


def test_nonpositive_prices_are_rejected() -> None:
    history = pd.DataFrame({"Close": [100.0, 0.0]})

    with pytest.raises(ValueError, match="strictly positive"):
        calculate_asset_returns(history)


def test_universe_returns_align_assets_by_date() -> None:
    spy = pd.DataFrame(
        {"Close": [100.0, 110.0]},
        index=pd.to_datetime(["2025-01-02", "2025-01-03"]),
    )
    tlt = pd.DataFrame(
        {"Close": [200.0, 220.0]},
        index=pd.to_datetime(["2025-01-03", "2025-01-06"]),
    )

    result = calculate_universe_returns(
        {"SPY": spy, "TLT": tlt},
        return_type="simple",
        price_column="Close",
    )

    assert list(result.columns) == ["SPY", "TLT"]
    assert pd.isna(result.loc[pd.Timestamp("2025-01-02"), "SPY"])
    assert pd.isna(result.loc[pd.Timestamp("2025-01-03"), "TLT"])
    assert result.loc[pd.Timestamp("2025-01-03"), "SPY"] == pytest.approx(0.10)
    assert result.loc[pd.Timestamp("2025-01-06"), "TLT"] == pytest.approx(0.10)


def test_invalid_return_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="return_type"):
        calculate_universe_returns(
            {"SPY": sample_history()},
            return_type="annual",
        )


def test_empty_universe_is_rejected() -> None:
    with pytest.raises(ValueError, match="At least one"):
        calculate_universe_returns({})