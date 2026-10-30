import numpy as np
import pandas as pd
import pytest

from project_structure.portfolio.max_sharpe import calculate_maximum_sharpe_weights


@pytest.fixture
def covariance() -> pd.DataFrame:
    return pd.DataFrame(
        [[0.01, 0.00], [0.00, 0.01]],
        index=["A", "B"],
        columns=["A", "B"],
    )


def test_weights_sum_to_one_and_are_long_only(
    covariance: pd.DataFrame,
) -> None:
    weights = calculate_maximum_sharpe_weights(
        {"A": 0.01, "B": 0.02},
        covariance,
    )

    assert np.isclose(weights.sum(), 1.0)
    assert (weights >= 0.0).all()
    assert (weights <= 1.0).all()


def test_prefers_higher_return_for_equal_risk(
    covariance: pd.DataFrame,
) -> None:
    weights = calculate_maximum_sharpe_weights(
        {"A": 0.01, "B": 0.02},
        covariance,
    )

    assert weights["B"] > weights["A"]
    assert weights["A"] == pytest.approx(1 / 3, abs=1e-5)
    assert weights["B"] == pytest.approx(2 / 3, abs=1e-5)


def test_preserves_covariance_asset_order() -> None:
    covariance = pd.DataFrame(
        [[0.01, 0.00], [0.00, 0.01]],
        index=["B", "A"],
        columns=["B", "A"],
    )

    weights = calculate_maximum_sharpe_weights(
        pd.Series({"A": 0.02, "B": 0.01}),
        covariance,
    )

    assert list(weights.index) == ["B", "A"]
    assert weights["A"] > weights["B"]


def test_accepts_nonzero_risk_free_rate(
    covariance: pd.DataFrame,
) -> None:
    weights = calculate_maximum_sharpe_weights(
        {"A": 0.02, "B": 0.04},
        covariance,
        risk_free_rate=0.01,
    )

    assert np.isclose(weights.sum(), 1.0)
    assert weights["B"] > weights["A"]


def test_rejects_mismatched_assets(
    covariance: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="must match"):
        calculate_maximum_sharpe_weights(
            {"A": 0.01, "C": 0.02},
            covariance,
        )


def test_rejects_non_finite_expected_returns(
    covariance: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="finite"):
        calculate_maximum_sharpe_weights(
            {"A": np.nan, "B": 0.02},
            covariance,
        )


def test_rejects_non_finite_risk_free_rate(
    covariance: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="finite"):
        calculate_maximum_sharpe_weights(
            {"A": 0.01, "B": 0.02},
            covariance,
            risk_free_rate=np.inf,
        )


def test_rejects_zero_covariance() -> None:
    covariance = pd.DataFrame(
        [[0.0, 0.0], [0.0, 0.0]],
        index=["A", "B"],
        columns=["A", "B"],
    )

    with pytest.raises(ValueError, match="zero covariance"):
        calculate_maximum_sharpe_weights(
            {"A": 0.01, "B": 0.02},
            covariance,
        )