import numpy as np
import pandas as pd
import pytest

from project_structure.portfolio.optimization import (
    calculate_equal_weights,
    calculate_minimum_variance_weights,
)


def test_equal_weights_are_correct() -> None:
    weights = calculate_equal_weights(["SPY", "TLT", "GLD"])

    assert np.allclose(weights.to_numpy(), [1 / 3, 1 / 3, 1 / 3])
    assert np.isclose(weights.sum(), 1.0)


def test_equal_weights_reject_empty_assets() -> None:
    with pytest.raises(ValueError, match="At least one asset"):
        calculate_equal_weights([])


def test_equal_weights_reject_duplicates() -> None:
    with pytest.raises(ValueError, match="unique"):
        calculate_equal_weights(["SPY", "SPY"])


def test_minimum_variance_weights_sum_to_one() -> None:
    covariance = pd.DataFrame(
        [[0.04, 0.00], [0.00, 0.01]],
        index=["A", "B"],
        columns=["A", "B"],
    )

    weights = calculate_minimum_variance_weights(covariance)

    assert np.isclose(weights.sum(), 1.0)
    assert (weights >= 0.0).all()
    assert (weights <= 1.0).all()


def test_minimum_variance_prefers_lower_risk_uncorrelated_asset() -> None:
    covariance = pd.DataFrame(
        [[0.04, 0.00], [0.00, 0.01]],
        index=["A", "B"],
        columns=["A", "B"],
    )

    weights = calculate_minimum_variance_weights(covariance)

    assert weights["B"] > weights["A"]
    assert weights["A"] == pytest.approx(0.20, abs=1e-5)
    assert weights["B"] == pytest.approx(0.80, abs=1e-5)


def test_weights_follow_covariance_asset_labels() -> None:
    covariance = pd.DataFrame(
        [[0.01, 0.00], [0.00, 0.04]],
        index=["TLT", "SPY"],
        columns=["TLT", "SPY"],
    )

    weights = calculate_minimum_variance_weights(covariance)

    assert list(weights.index) == ["TLT", "SPY"]
    assert weights["TLT"] > weights["SPY"]


def test_rejects_non_square_covariance() -> None:
    covariance = pd.DataFrame([[0.01, 0.00]], columns=["A", "B"])

    with pytest.raises(ValueError, match="square"):
        calculate_minimum_variance_weights(covariance)


def test_rejects_asymmetric_covariance() -> None:
    covariance = pd.DataFrame(
        [[0.04, 0.01], [0.02, 0.01]],
        index=["A", "B"],
        columns=["A", "B"],
    )

    with pytest.raises(ValueError, match="symmetric"):
        calculate_minimum_variance_weights(covariance)


def test_rejects_non_finite_covariance() -> None:
    covariance = pd.DataFrame(
        [[0.04, np.nan], [np.nan, 0.01]],
        index=["A", "B"],
        columns=["A", "B"],
    )

    with pytest.raises(ValueError, match="non-finite"):
        calculate_minimum_variance_weights(covariance)


def test_rejects_non_positive_semidefinite_covariance() -> None:
    covariance = pd.DataFrame(
        [[0.01, 0.03], [0.03, 0.01]],
        index=["A", "B"],
        columns=["A", "B"],
    )

    with pytest.raises(ValueError, match="positive semidefinite"):
        calculate_minimum_variance_weights(covariance)