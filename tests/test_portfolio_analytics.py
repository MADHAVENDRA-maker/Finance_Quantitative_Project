import numpy as np
import pandas as pd
import pytest

from project_structure.portfolio.analytics import (
    calculate_portfolio_returns,
    calculate_portfolio_volatility,
    validate_portfolio_weights,
)


def test_valid_weights_are_preserved() -> None:
    weights = validate_portfolio_weights({"SPY": 0.6, "TLT": 0.4})
    assert weights["SPY"] == pytest.approx(0.6)
    assert weights["TLT"] == pytest.approx(0.4)
    assert weights.sum() == pytest.approx(1.0)


def test_weights_not_summing_to_one_are_rejected() -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        validate_portfolio_weights({"SPY": 0.6, "TLT": 0.3})


def test_non_finite_weights_are_rejected() -> None:
    with pytest.raises(ValueError, match="finite"):
        validate_portfolio_weights({"SPY": np.nan, "TLT": 1.0})


def test_empty_weights_are_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        validate_portfolio_weights({})


def test_portfolio_returns_are_weighted_sum() -> None:
    returns = pd.DataFrame(
        {"SPY": [0.10, -0.05], "TLT": [0.02, 0.01]}
    )
    weights = {"SPY": 0.6, "TLT": 0.4}

    result = calculate_portfolio_returns(returns, weights)

    assert result.iloc[0] == pytest.approx(0.068)
    assert result.iloc[1] == pytest.approx(-0.026)
    assert result.name == "portfolio_return"


def test_portfolio_returns_align_columns_by_asset_name() -> None:
    returns = pd.DataFrame(
        {"TLT": [0.02], "SPY": [0.10]}
    )
    result = calculate_portfolio_returns(
        returns, {"SPY": 0.6, "TLT": 0.4}
    )
    assert result.iloc[0] == pytest.approx(0.068)


def test_portfolio_returns_reject_missing_observations() -> None:
    returns = pd.DataFrame(
        {"SPY": [0.01], "TLT": [np.nan]}
    )
    with pytest.raises(ValueError, match="missing observations"):
        calculate_portfolio_returns(returns, {"SPY": 0.6, "TLT": 0.4})


def test_portfolio_returns_reject_mismatched_assets() -> None:
    returns = pd.DataFrame({"SPY": [0.01], "QQQ": [0.02]})
    with pytest.raises(ValueError, match="must match"):
        calculate_portfolio_returns(returns, {"SPY": 0.6, "TLT": 0.4})


def test_portfolio_volatility_matches_manual_calculation() -> None:
    covariance = pd.DataFrame(
        [[0.04, 0.01], [0.01, 0.09]],
        index=["SPY", "TLT"],
        columns=["SPY", "TLT"],
    )
    weights = {"SPY": 0.6, "TLT": 0.4}

    result = calculate_portfolio_volatility(
        covariance, weights, periods_per_year=1
    )

    expected_variance = (
        0.6**2 * 0.04
        + 0.4**2 * 0.09
        + 2 * 0.6 * 0.4 * 0.01
    )
    assert result == pytest.approx(np.sqrt(expected_variance))


def test_portfolio_volatility_annualizes_correctly() -> None:
    covariance = pd.DataFrame(
        [[0.0001]],
        index=["SPY"],
        columns=["SPY"],
    )
    result = calculate_portfolio_volatility(
        covariance, {"SPY": 1.0}, periods_per_year=252
    )
    assert result == pytest.approx(np.sqrt(0.0001 * 252))


def test_portfolio_volatility_rejects_mismatched_assets() -> None:
    covariance = pd.DataFrame(
        [[0.04]],
        index=["SPY"],
        columns=["SPY"],
    )
    with pytest.raises(ValueError, match="must match"):
        calculate_portfolio_volatility(
            covariance, {"SPY": 0.6, "TLT": 0.4}
        )


def test_portfolio_volatility_rejects_asymmetric_covariance() -> None:
    covariance = pd.DataFrame(
        [[0.04, 0.01], [0.02, 0.09]],
        index=["SPY", "TLT"],
        columns=["SPY", "TLT"],
    )
    with pytest.raises(ValueError, match="symmetric"):
        calculate_portfolio_volatility(
            covariance, {"SPY": 0.6, "TLT": 0.4}
        )