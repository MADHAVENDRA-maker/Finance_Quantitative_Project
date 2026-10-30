from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from project_structure.features.relationships import calculate_rolling_correlation


def plot_correlation_heatmap(
    correlation: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """Plot and save a correlation matrix as a heatmap."""
    if not isinstance(correlation, pd.DataFrame):
        raise TypeError("Correlation must be supplied as a pandas DataFrame.")

    if correlation.empty or correlation.shape[0] != correlation.shape[1]:
        raise ValueError("Correlation must be a non-empty square matrix.")

    if correlation.index.has_duplicates or correlation.columns.has_duplicates:
        raise ValueError("Correlation matrix labels must be unique.")

    if list(correlation.index) != list(correlation.columns):
        raise ValueError("Correlation matrix row and column labels must match.")

    try:
        values = correlation.to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Correlation matrix must contain numeric values.") from exc

    if not np.isfinite(values).all():
        raise ValueError("Correlation matrix contains missing or non-finite values.")

    if (values < -1).any() or (values > 1).any():
        raise ValueError("Correlation values must lie between -1 and 1.")

    if not np.allclose(values, values.T, atol=1e-8):
        raise ValueError("Correlation matrix must be symmetric.")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    labels = [str(label) for label in correlation.columns]
    figure_size = max(6, len(labels) * 0.8)

    fig, ax = plt.subplots(figsize=(figure_size, figure_size * 0.85))
    image = ax.imshow(values, vmin=-1, vmax=1, cmap="coolwarm")

    ax.set_xticks(range(len(labels)), labels=labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)), labels=labels)
    ax.set_title("Asset Return Correlation Matrix")

    for row in range(len(labels)):
        for column in range(len(labels)):
            ax.text(
                column,
                row,
                f"{values[row, column]:.2f}",
                ha="center",
                va="center",
                color="black",
            )

    fig.colorbar(image, ax=ax, label="Pearson correlation")
    fig.tight_layout()
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output


def plot_rolling_correlation(
    returns: pd.DataFrame,
    asset_1: str,
    asset_2: str,
    output_path: str | Path,
    window: int = 60,
) -> Path:
    """Plot and save rolling correlation between two assets."""
    rolling = calculate_rolling_correlation(
        returns=returns,
        asset_1=asset_1,
        asset_2=asset_2,
        window=window,
    )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(rolling.index, rolling.values, label=f"{asset_1} vs {asset_2}")

    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_ylim(-1.05, 1.05)
    ax.set_title(
        f"{window}-Observation Rolling Correlation: {asset_1} vs {asset_2}"
    )
    ax.set_xlabel("Date")
    ax.set_ylabel("Pearson correlation")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output