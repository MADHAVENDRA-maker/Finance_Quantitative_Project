import pytest
from project_structure.stress_testing.engine import (calculate_stress_impact)



def test_weighted_stress_impact():
    detail, summary = calculate_stress_impact(
        weights={"SPY": 0.60, "GLD": 0.40},
        shocks={"SPY": -0.20, "GLD": 0.05},
        portfolio_value=1_000_000,
    )

    assert summary["portfolio_return"] == pytest.approx(-0.10)
    assert summary["estimated_pnl"] == pytest.approx(-100_000)
    assert summary["stressed_value"] == pytest.approx(900_000)

    assert detail.loc["SPY", "portfolio_contribution"] == pytest.approx(-0.12)
    assert detail.loc["GLD", "portfolio_contribution"] == pytest.approx(0.02)


def test_engine_rejects_weights_not_summing_to_one():
    with pytest.raises(ValueError, match="sum to 1"):
        calculate_stress_impact(
            weights={"SPY": 0.60, "GLD": 0.30},
            shocks={"SPY": -0.20, "GLD": 0.05},
        )


def test_engine_rejects_shocks_below_total_loss():
    with pytest.raises(ValueError, match="-100%"):
        calculate_stress_impact(
            weights={"SPY": 1.0},
            shocks={"SPY": -1.10},
        )