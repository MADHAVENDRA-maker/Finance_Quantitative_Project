from collections.abc import Mapping
import numpy as np
import pandas as pd


def calculate_stress_impact(
    weights: pd.Series | Mapping[str, float],
    shocks: pd.Series | Mapping[str, float],
    portfolio_value: float = 1_000_000.0,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """
    Calculate deterministic portfolio impact under asset-level shocks.

    Weights must sum to 1. Shocks are simple returns expressed as
    decimals: -0.20 means a 20% decline; 0.05 means a 5% gain.
    """
    if isinstance(weights, Mapping):
        weights = pd.Series(dict(weights), dtype=float)
    elif isinstance(weights, pd.Series):
        weights = weights.copy()
    else:
        raise TypeError("Weights must be a Series or mapping.")

    if isinstance(shocks, Mapping):
        shocks = pd.Series(dict(shocks), dtype=float)
    elif isinstance(shocks, pd.Series):
        shocks = shocks.copy()
    else:
        raise TypeError("Shocks must be a Series or mapping.")

    if weights.empty:
        raise ValueError("At least one portfolio asset is required.")

    if weights.index.has_duplicates or shocks.index.has_duplicates:
        raise ValueError("Asset names must be unique.")

    if set(weights.index) != set(shocks.index):
        raise ValueError("Weights and shocks must contain the same assets.")

    weights = weights.astype(float)
    shocks = shocks.reindex(weights.index).astype(float)

    if not np.isfinite(weights.to_numpy()).all():
        raise ValueError("Weights must be finite.")

    if not np.isfinite(shocks.to_numpy()).all():
        raise ValueError("Shocks must be finite.")

    if (weights < 0).any():
        raise ValueError("This engine supports long-only portfolios.")

    if not np.isclose(weights.sum(), 1.0, atol=1e-8):
        raise ValueError("Portfolio weights must sum to 1.")

    if (shocks < -1.0).any():
        raise ValueError("An asset shock cannot be below -100%.")

    if (
        not np.isfinite(portfolio_value)
        or portfolio_value <= 0
    ):
        raise ValueError("Portfolio value must be positive and finite.")

    contribution = weights * shocks
    pnl = contribution * portfolio_value

    result = pd.DataFrame(
        {
            "weight": weights,
            "asset_shock": shocks,
            "portfolio_contribution": contribution,
            "estimated_pnl": pnl,
        }
    )
    result.index.name = "asset"

    portfolio_return = float(contribution.sum())
    estimated_pnl = float(portfolio_return * portfolio_value)
    stressed_value = float(portfolio_value + estimated_pnl)

    summary = {
        "portfolio_return": portfolio_return,
        "estimated_pnl": estimated_pnl,
        "initial_value": float(portfolio_value),
        "stressed_value": stressed_value,
    }

    return result, summary