from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from project_structure.backtesting.rolling_metrics import (
    calculate_rolling_sharpe,
    calculate_rolling_volatility,
)


def _validate_backtest_results(
    results: dict[str, pd.DataFrame],
) -> None:
    """Validate strategy results before plotting."""
    if not isinstance(results, dict) or not results:
        raise ValueError("Provide at least one strategy result.")

    for name, frame in results.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Strategy names must be non-empty strings.")

        if not isinstance(frame, pd.DataFrame):
            raise TypeError("Each strategy result must be a DataFrame.")

        if frame.empty:
            raise ValueError(f"Results for {name} cannot be empty.")

        if "net_return" not in frame.columns:
            raise ValueError(f"Results for {name} need a net_return column.")

        returns = frame["net_return"].to_numpy(dtype=float)

        if not np.isfinite(returns).all():
            raise ValueError(f"Net returns for {name} must be finite.")

        if (returns < -1.0).any():
            raise ValueError(f"Net returns for {name} cannot be below -100%.")


def plot_cumulative_returns(
    results: dict[str, pd.DataFrame],
    output_dir: str | Path,
) -> Path:
    """Plot cumulative net returns for all strategies."""
    _validate_backtest_results(results)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))

    for name, frame in results.items():
        cumulative_returns = (1.0 + frame["net_return"]).cumprod() - 1.0
        ax.plot(
            frame.index,
            cumulative_returns * 100.0,
            label=name,
            linewidth=1.5,
        )

    ax.set_title("Cumulative Out-of-Sample Net Returns")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative return (%)")
    ax.axhline(0.0, linewidth=0.8, linestyle="--")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    output_path = output_dir / "backtest_cumulative_returns.png"
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    return output_path


def plot_drawdowns(
    results: dict[str, pd.DataFrame],
    output_dir: str | Path,
) -> Path:
    """Plot drawdowns from each strategy's previous wealth peak."""
    _validate_backtest_results(results)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))

    for name, frame in results.items():
        wealth = (1.0 + frame["net_return"]).cumprod()
        wealth_with_initial_value = pd.concat(
            [
                pd.Series([1.0], index=[frame.index[0] - pd.Timedelta(days=1)]),
                wealth,
            ]
        )
        running_peak = wealth_with_initial_value.cummax().iloc[1:]
        drawdowns = wealth / running_peak - 1.0

        ax.plot(
            frame.index,
            drawdowns * 100.0,
            label=name,
            linewidth=1.3,
        )

    ax.set_title("Out-of-Sample Portfolio Drawdowns")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown (%)")
    ax.axhline(0.0, linewidth=0.8, linestyle="--")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    output_path = output_dir / "backtest_drawdowns.png"
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    return output_path

def plot_rolling_sharpe(
    results: dict[str, pd.DataFrame],
    output_dir: str | Path,
    window: int = 63,
    risk_free_rate: float = 0.0,
) -> Path:
    """Plot annualized rolling Sharpe ratios for all strategies."""
    _validate_backtest_results(results)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))

    for name, frame in results.items():
        rolling_sharpe = calculate_rolling_sharpe(
            frame["net_return"],
            window=window,
            risk_free_rate=risk_free_rate,
        )

        ax.plot(
            frame.index,
            rolling_sharpe,
            label=name,
            linewidth=1.3,
        )

    ax.set_title(f"Rolling Sharpe Ratio ({window}-Trading-Day Window)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Annualized Sharpe ratio")
    ax.axhline(0.0, linewidth=0.8, linestyle="--")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    output_path = output_dir / "backtest_rolling_sharpe.png"
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    return output_path


def plot_rolling_volatility(
    results: dict[str, pd.DataFrame],
    output_dir: str | Path,
    window: int = 63,
) -> Path:
    """Plot annualized rolling volatility for all strategies."""
    _validate_backtest_results(results)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))

    for name, frame in results.items():
        rolling_volatility = calculate_rolling_volatility(
            frame["net_return"],
            window=window,
        )

        ax.plot(
            frame.index,
            rolling_volatility * 100.0,
            label=name,
            linewidth=1.3,
        )

    ax.set_title(f"Rolling Annualized Volatility ({window}-Trading-Day Window)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Annualized volatility (%)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    output_path = output_dir / "backtest_rolling_volatility.png"
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    return output_path

def plot_allocation_weights(
    results: dict[str, pd.DataFrame],
    output_dir: str | Path,
) -> Path:
    """Plot daily allocation weights for every asset across strategies."""
    _validate_backtest_results(results)

    if not results:
        raise ValueError("At least one backtest result is required.")

    weight_columns = sorted(
        column
        for column in next(iter(results.values())).columns
        if column.startswith("weight_")
    )

    if not weight_columns:
        raise ValueError("No portfolio weight columns were found.")

    expected_columns = set(weight_columns)

    for name, frame in results.items():
        available_columns = {
            column
            for column in frame.columns
            if column.startswith("weight_")
        }

        if available_columns != expected_columns:
            raise ValueError(
                f"Results for {name} must contain the same weight columns "
                f"as the other strategies."
            )

        weights = frame[weight_columns].to_numpy(dtype=float)

        if not np.isfinite(weights).all():
            raise ValueError(f"Weights for {name} must be finite.")

        if (weights < -1e-8).any() or (weights > 1.0 + 1e-8).any():
            raise ValueError(
                f"Weights for {name} must be between 0 and 1."
            )

        if not np.allclose(weights.sum(axis=1), 1.0, atol=1e-6):
            raise ValueError(
                f"Portfolio weights for {name} must sum to 1."
            )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    columns = 2
    rows = (len(weight_columns) + columns - 1) // columns

    fig, axes = plt.subplots(
        rows,
        columns,
        figsize=(16, 3.2 * rows),
        sharex=True,
        squeeze=False,
    )
    axes_flat = axes.flatten()

    for ax, weight_column in zip(axes_flat, weight_columns):
        ticker = weight_column.removeprefix("weight_")

        for strategy_name, frame in results.items():
            ax.plot(
                frame.index,
                frame[weight_column] * 100.0,
                label=strategy_name,
                linewidth=1.0,
            )

        ax.set_title(f"{ticker} Allocation")
        ax.set_ylabel("Portfolio weight (%)")
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

    for ax in axes_flat[len(weight_columns):]:
        ax.set_visible(False)

    for ax in axes_flat[:len(weight_columns)]:
        ax.set_xlabel("Date")

    fig.suptitle("Daily Portfolio Allocation by Strategy", y=1.002)
    fig.tight_layout()

    output_path = output_dir / "backtest_allocation_weights.png"
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    return output_path


def plot_strategy_turnover(
    results: dict[str, pd.DataFrame],
    output_dir: str | Path,
) -> Path:
    """Plot daily portfolio turnover for each strategy."""
    _validate_backtest_results(results)

    for name, frame in results.items():
        if "turnover" not in frame.columns:
            raise ValueError(
                f"Results for {name} need a turnover column."
            )

        turnover = frame["turnover"].to_numpy(dtype=float)

        if not np.isfinite(turnover).all() or (turnover < 0).any():
            raise ValueError(
                f"Turnover for {name} must be finite and non-negative."
            )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(13, 6))

    for name, frame in results.items():
        ax.plot(
            frame.index,
            frame["turnover"] * 100.0,
            label=name,
            linewidth=1.0,
            alpha=0.85,
        )

    ax.set_title("Daily Portfolio Turnover by Strategy")
    ax.set_xlabel("Date")
    ax.set_ylabel("Turnover (% of portfolio)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    output_path = output_dir / "backtest_strategy_turnover.png"
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    return output_path