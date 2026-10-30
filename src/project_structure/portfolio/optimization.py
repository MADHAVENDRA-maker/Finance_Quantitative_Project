import numpy as np
import pandas as pd
from scipy.optimize import minimize


def _validate_covariance_matrix(covariance: pd.DataFrame) -> pd.DataFrame:
    """Validate and return a numeric covariance matrix."""
    if not isinstance(covariance, pd.DataFrame):
        raise TypeError("Covariance must be supplied as a pandas DataFrame.")

    if covariance.empty or covariance.shape[0] != covariance.shape[1]:
        raise ValueError("Covariance must be a non-empty square matrix.")

    if covariance.index.has_duplicates or covariance.columns.has_duplicates:
        raise ValueError("Covariance matrix labels must be unique.")

    if list(covariance.index) != list(covariance.columns):
        raise ValueError("Covariance row and column labels must match.")

    if not all(
        isinstance(asset, str) and asset.strip()
        for asset in covariance.index
    ):
        raise ValueError("Asset names must be non-empty strings.")

    try:
        values = covariance.to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Covariance matrix must be numeric.") from exc

    if not np.isfinite(values).all():
        raise ValueError("Covariance matrix contains non-finite values.")

    if not np.allclose(values, values.T, rtol=1e-7, atol=1e-12):
        raise ValueError("Covariance matrix must be symmetric.")

    # A covariance matrix must be positive semidefinite.
    eigenvalues = np.linalg.eigvalsh(values)
    scale = max(float(np.max(np.abs(values))), 1e-15)

    if float(eigenvalues.min()) < -1e-10 * scale:
        raise ValueError("Covariance matrix must be positive semidefinite.")

    return pd.DataFrame(
        values,
        index=covariance.index.copy(),
        columns=covariance.columns.copy(),
    )


def calculate_equal_weights(
    assets: list[str] | tuple[str, ...],
) -> pd.Series:
    """Return an equal-weight allocation for the supplied assets."""
    if not assets:
        raise ValueError("At least one asset is required.")

    if any(not isinstance(asset, str) or not asset.strip() for asset in assets):
        raise ValueError("Asset names must be non-empty strings.")

    if len(set(assets)) != len(assets):
        raise ValueError("Asset names must be unique.")

    weights = pd.Series(
        1.0 / len(assets),
        index=pd.Index(assets, name="ticker"),
        dtype=float,
        name="weight",
    )
    return weights


def calculate_minimum_variance_weights(
    covariance: pd.DataFrame,
) -> pd.Series:
    """Find long-only weights that minimize portfolio variance.

    The covariance matrix must represent periodic return covariance.
    Each weight is constrained to [0, 1], and weights must sum to 1.
    """
    covariance = _validate_covariance_matrix(covariance)
    assets = list(covariance.columns)
    matrix = covariance.to_numpy(dtype=float)
    n_assets = len(assets)

    initial_weights = np.full(n_assets, 1.0 / n_assets)

    def objective(weights: np.ndarray) -> float:
        return float(weights @ matrix @ weights)

    result = minimize(
        objective,
        initial_weights,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n_assets,
        constraints=[
            {
                "type": "eq",
                "fun": lambda weights: float(np.sum(weights) - 1.0),
            }
        ],
        options={"maxiter": 1000, "ftol": 1e-12},
    )

    if not result.success:
        raise RuntimeError(
            f"Minimum-variance optimization failed: {result.message}"
        )

    weights = np.asarray(result.x, dtype=float)

    if not np.isfinite(weights).all():
        raise RuntimeError("Optimizer returned non-finite weights.")

    # Verify constraints rather than silently accepting an invalid solution.
    if (
        np.any(weights < -1e-7)
        or np.any(weights > 1.0 + 1e-7)
        or not np.isclose(weights.sum(), 1.0, atol=1e-7)
    ):
        raise RuntimeError("Optimizer returned weights outside the constraints.")

    # Remove only tiny numerical deviations from the feasible region.
    weights = np.clip(weights, 0.0, 1.0)
    weights /= weights.sum()

    return pd.Series(
        weights,
        index=pd.Index(assets, name="ticker"),
        dtype=float,
        name="weight",
    )