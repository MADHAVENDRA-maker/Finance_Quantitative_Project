import numpy as np
import pandas as pd
import pytest

from project_structure.features.relationships import (
    calculate_correlation_matrix,
    calculate_covariance_matrix,
    calculate_rolling_correlation,
)


@pytest.fixture
def sample_returns() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "SPY": [0.01, 0.02, -0.01, 0.03, -0.02],
            "TLT": [-0.005, 0.01, 0.02, -0.01, 0.005],
        }
    )


def test_correlation_matrix_has_expected_shape(
    sample_returns: pd.DataFrame,
) -> None:
    result = calculate_correlation_matrix(sample_returns)
    assert result.shape == (2, 2)
    assert list(result.index) == ["SPY", "TLT"]


def test_correlation_matrix_is_symmetric(
    sample_returns: pd.DataFrame,
) -> None:
    result = calculate_correlation_matrix(sample_returns)
    np.testing.assert_allclose(result.to_numpy(), result.to_numpy().T)
    np.testing.assert_allclose(np.diag(result), [1.0, 1.0])


def test_correlation_values_are_within_valid_range(
    sample_returns: pd.DataFrame,
) -> None:
    result = calculate_correlation_matrix(sample_returns)
    assert (result.to_numpy() >= -1.0).all()
    assert (result.to_numpy() <= 1.0).all()


def test_covariance_matrix_is_symmetric(
    sample_returns: pd.DataFrame,
) -> None:
    result = calculate_covariance_matrix(sample_returns)
    np.testing.assert_allclose(result.to_numpy(), result.to_numpy().T)


def test_covariance_diagonal_matches_sample_variance(
    sample_returns: pd.DataFrame,
) -> None:
    result = calculate_covariance_matrix(sample_returns)
    for ticker in sample_returns.columns:
        assert result.loc[ticker, ticker] == pytest.approx(
            sample_returns[ticker].var(ddof=1)
        )


def test_rolling_correlation_has_expected_warmup(
    sample_returns: pd.DataFrame,
) -> None:
    result = calculate_rolling_correlation(
        sample_returns, "SPY", "TLT", window=3
    )
    assert result.iloc[:2].isna().all()
    assert result.iloc[2:].notna().all()


def test_rolling_correlation_is_bounded(
    sample_returns: pd.DataFrame,
) -> None:
    result = calculate_rolling_correlation(
        sample_returns, "SPY", "TLT", window=3
    )
    assert (result.dropna() >= -1.0).all()
    assert (result.dropna() <= 1.0).all()


def test_missing_values_are_rejected(
    sample_returns: pd.DataFrame,
) -> None:
    sample_returns.loc[2, "SPY"] = np.nan
    with pytest.raises(ValueError, match="missing observations"):
        calculate_correlation_matrix(sample_returns)


def test_constant_asset_is_rejected(
    sample_returns: pd.DataFrame,
) -> None:
    sample_returns["CONSTANT"] = 0.01
    with pytest.raises(ValueError, match="zero variance"):
        calculate_covariance_matrix(sample_returns)


def test_invalid_rolling_window_is_rejected(
    sample_returns: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="window"):
        calculate_rolling_correlation(
            sample_returns, "SPY", "TLT", window=1
        )


def test_unknown_asset_is_rejected(
    sample_returns: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="Both assets"):
        calculate_rolling_correlation(
            sample_returns, "SPY", "UNKNOWN", window=3
        )