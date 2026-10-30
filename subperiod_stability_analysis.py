from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from project_structure.features.performance import calculate_performance_metrics

PROJECT_ROOT = Path(__file__).resolve().parent
ROBUSTNESS_DIR = PROJECT_ROOT / "data" / "runs" / "robustness"
OUTPUT_DIR = ROBUSTNESS_DIR / "subperiod_stability"

BASELINE_REBALANCE = 21
BASELINE_COST_BPS = 10


def load_backtest_results() -> dict[str, pd.DataFrame]:
    """Load all individual robustness backtest CSV files."""
    files = sorted(
        ROBUSTNESS_DIR.glob("*_rebalance_*_cost_*bps.csv")
    )

    if not files:
        raise FileNotFoundError(
            f"No robustness backtest CSV files found in {ROBUSTNESS_DIR}. "
            "Run robustness_analysis.py first."
        )

    results = {}

    for path in files:
        parts = path.stem.split("_rebalance_")
        if len(parts) != 2:
            raise ValueError(f"Unexpected filename format: {path.name}")

        strategy_name = parts[0].replace("_", " ").title()
        rebalance_part, cost_part = parts[1].split("_cost_")
        rebalance_every = int(rebalance_part)
        cost_bps = int(cost_part.removesuffix("bps"))

        label = (
            f"{strategy_name} | {rebalance_every}-day rebalance "
            f"| {cost_bps} bps"
        )

        frame = pd.read_csv(path)

        if "Date" not in frame.columns:
            raise ValueError(
                f"'Date' column missing from {path.name}. "
                f"Available columns: {frame.columns.tolist()}"
            )

        frame["Date"] = pd.to_datetime(
            frame["Date"],
            errors="raise",
            utc=True
        )

        frame = (
            frame
            .set_index("Date")
            .sort_index()
        )

        if not isinstance(frame.index, pd.DatetimeIndex):
            raise TypeError(
                f"Expected DatetimeIndex in {path.name}, "
                f"got {type(frame.index).__name__}"
            )
        frame.index = frame.index.tz_localize(None)

        if frame.empty:
            raise ValueError(f"Backtest file is empty: {path.name}")

        if "net_return" not in frame.columns:
            raise ValueError(
                f"'net_return' column missing from {path.name}"
            )

        returns = frame["net_return"]

        if (
            returns.isna().any()
            or not np.isfinite(returns.to_numpy()).all()
            or (returns < -1.0).any()
        ):
            raise ValueError(
                f"Invalid net returns found in {path.name}"
            )

        if not frame.index.is_unique:
            raise ValueError(
                f"Duplicate dates found in {path.name}"
            )

        results[label] = {
            "frame": frame,
            "strategy": strategy_name,
            "rebalance_every": rebalance_every,
            "transaction_cost_bps": cost_bps,
        }

    if len(results) != 27:
        raise ValueError(
            f"Expected 27 backtest files, found {len(results)}."
        )

    return results


def calculate_yearly_metrics(
    results: dict[str, dict],
) -> pd.DataFrame:
    """Calculate metrics independently for each calendar year."""
    rows = []

    for label, info in results.items():
        frame = info["frame"]

        for year, yearly_frame in frame.groupby(frame.index.year):
            returns = yearly_frame["net_return"]
            metrics = calculate_performance_metrics(returns)

            # The compounded return is the actual return for the
            # observations available in this calendar year.
            actual_period_return = float(
                (1.0 + returns).prod() - 1.0
            )

            rows.append(
                {
                    "configuration": label,
                    "strategy": info["strategy"],
                    "rebalance_every": info["rebalance_every"],
                    "transaction_cost_bps": (
                        info["transaction_cost_bps"]
                    ),
                    "year": int(year),
                    "observations": len(returns),
                    "start_date": yearly_frame.index.min().date().isoformat(),
                    "end_date": yearly_frame.index.max().date().isoformat(),
                    "period_return": actual_period_return,
                    "annualized_return": float(
                        metrics["annualized_return"]
                    ),
                    "annualized_volatility": float(
                        metrics["annualized_volatility"]
                    ),
                    "sharpe_ratio": float(metrics["sharpe_ratio"]),
                    "maximum_drawdown": float(
                        metrics["maximum_drawdown"]
                    ),
                }
            )

    return pd.DataFrame(rows).sort_values(
        ["year", "strategy", "rebalance_every",
         "transaction_cost_bps"]
    )


def plot_baseline_annual_returns(
    yearly: pd.DataFrame,
) -> None:
    """Plot actual calendar-year returns for baseline configurations."""
    baseline = yearly[
        (yearly["rebalance_every"] == BASELINE_REBALANCE)
        & (yearly["transaction_cost_bps"] == BASELINE_COST_BPS)
    ]

    pivot = baseline.pivot(
        index="year",
        columns="strategy",
        values="period_return",
    )

    ax = pivot.plot(
        kind="bar",
        figsize=(12, 6),
        width=0.8,
    )
    ax.axhline(0, linewidth=0.8)
    ax.set_title(
        "Calendar-Year Portfolio Returns "
        "(21-Day Rebalancing, 10 bps Costs)"
    )
    ax.set_xlabel("Calendar year")
    ax.set_ylabel("Compounded return over available observations")
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda value, _: f"{value:.0%}")
    )
    ax.legend(title="Strategy")
    ax.grid(axis="y", alpha=0.3)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "baseline_annual_returns.png",
        dpi=160,
    )
    plt.close()


def plot_baseline_annual_sharpe(
    yearly: pd.DataFrame,
) -> None:
    """Plot annual Sharpe ratios for baseline configurations."""
    baseline = yearly[
        (yearly["rebalance_every"] == BASELINE_REBALANCE)
        & (yearly["transaction_cost_bps"] == BASELINE_COST_BPS)
    ]

    pivot = baseline.pivot(
        index="year",
        columns="strategy",
        values="sharpe_ratio",
    )

    ax = pivot.plot(
        kind="line",
        marker="o",
        figsize=(12, 6),
    )
    ax.axhline(0, linewidth=0.8)
    ax.set_title(
        "Calendar-Year Sharpe Ratio "
        "(21-Day Rebalancing, 10 bps Costs)"
    )
    ax.set_xlabel("Calendar year")
    ax.set_ylabel("Sharpe ratio")
    ax.legend(title="Strategy")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "baseline_annual_sharpe.png",
        dpi=160,
    )
    plt.close()


def plot_configuration_sharpe_heatmap(
    yearly: pd.DataFrame,
) -> None:
    """Compare annual Sharpe ratios across all 27 configurations."""
    pivot = yearly.pivot(
        index="configuration",
        columns="year",
        values="sharpe_ratio",
    )

    fig_height = max(9, len(pivot) * 0.34)
    fig, ax = plt.subplots(figsize=(12, fig_height))

    image = ax.imshow(
        pivot.to_numpy(dtype=float),
        aspect="auto",
        interpolation="nearest",
    )

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns.astype(str))
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=7)
    ax.set_title("Annual Sharpe Ratio Across Robustness Configurations")
    ax.set_xlabel("Calendar year")
    ax.set_ylabel("Configuration")

    fig.colorbar(image, ax=ax, label="Sharpe ratio")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "configuration_sharpe_heatmap.png",
        dpi=160,
    )
    plt.close()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = load_backtest_results()
    yearly = calculate_yearly_metrics(results)

    yearly.to_csv(
        OUTPUT_DIR / "annual_subperiod_metrics.csv",
        index=False,
    )

    yearly_returns = yearly.pivot(
        index=["configuration", "strategy",
               "rebalance_every", "transaction_cost_bps"],
        columns="year",
        values="period_return",
    )
    yearly_returns.to_csv(
        OUTPUT_DIR / "annual_returns_by_configuration.csv"
    )

    plot_baseline_annual_returns(yearly)
    plot_baseline_annual_sharpe(yearly)
    plot_configuration_sharpe_heatmap(yearly)

    baseline = yearly[
        (yearly["rebalance_every"] == BASELINE_REBALANCE)
        & (yearly["transaction_cost_bps"] == BASELINE_COST_BPS)
    ]

    print("=" * 76)
    print("SUBPERIOD STABILITY ANALYSIS")
    print("=" * 76)
    print(f"Configurations loaded: {len(results)}")
    print(f"Yearly metric rows: {len(yearly)}")
    print(
        f"Years covered: {yearly['year'].min()}–"
        f"{yearly['year'].max()}"
    )
    print()

    print("BASELINE: 21-DAY REBALANCING, 10 BPS COSTS")
    print(
        baseline[
            [
                "year",
                "strategy",
                "observations",
                "period_return",
                "annualized_volatility",
                "sharpe_ratio",
                "maximum_drawdown",
            ]
        ].to_string(index=False, float_format=lambda x: f"{x:.4f}")
    )

    print()
    print("Files saved to:")
    print(OUTPUT_DIR)
    print("- annual_subperiod_metrics.csv")
    print("- annual_returns_by_configuration.csv")
    print("- baseline_annual_returns.png")
    print("- baseline_annual_sharpe.png")
    print("- configuration_sharpe_heatmap.png")


if __name__ == "__main__":
    main()