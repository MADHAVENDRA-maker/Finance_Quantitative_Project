from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from backtest_allocations import LOOKBACK, STRATEGIES, load_asset_returns
from project_structure.backtesting.engine import run_backtest
from project_structure.features.performance import calculate_performance_metrics

ROOT = Path(__file__).resolve().parent
STATEFUL_DIR = ROOT / "data" / "runs" / "walk_forward_stateful"
OUTPUT_DIR = ROOT / "data" / "runs" / "walk_forward_comparison"

INTERVALS = (5, 21, 63)
COST_BPS = 10.0
INITIAL_SELECTION_YEARS = 2


def normalize_index(frame):
    frame = frame.copy()
    frame.index = pd.to_datetime(
        frame.index, errors="raise", utc=True
    ).tz_localize(None)
    return frame.sort_index()


def load_stateful_results():
    path = STATEFUL_DIR / "stateful_walk_forward_returns.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run stateful_walk_forward_validation.py first."
        )

    frame = pd.read_csv(path, parse_dates=["Date"])
    frame["Date"] = pd.to_datetime(
        frame["Date"], errors="raise", utc=True
    ).dt.tz_localize(None)

    return frame


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    asset_returns = normalize_index(load_asset_returns())
    stateful = load_stateful_results()

    # Infer the evaluation period from the stateful results.
    test_start = stateful["Date"].min()
    test_end = stateful["Date"].max()
    expected_dates = pd.DatetimeIndex(
        sorted(stateful["Date"].unique())
    )

    rows = []

    # Fixed-interval baselines use the same backtest engine, lookback,
    # transaction cost, and evaluation dates as the adaptive strategy.
    for strategy_name, strategy_function in STRATEGIES.items():
        for interval in INTERVALS:
            candidate = run_backtest(
                asset_returns=asset_returns,
                strategy=strategy_function,
                lookback=LOOKBACK,
                rebalance_every=interval,
                transaction_cost_bps=COST_BPS,
            )
            candidate = normalize_index(candidate)

            candidate = candidate.loc[
                (candidate.index >= test_start)
                & (candidate.index <= test_end)
            ]

            if not candidate.index.equals(expected_dates):
                raise ValueError(
                    f"Date mismatch for {strategy_name}, interval {interval}."
                )

            for date, record in candidate.iterrows():
                rows.append(
                    {
                        "Date": date,
                        "strategy": strategy_name,
                        "approach": f"Fixed {interval}-day",
                        "net_return": float(record["net_return"]),
                        "gross_return": float(record["gross_return"]),
                        "turnover": float(record["turnover"]),
                        "transaction_cost": float(
                            record["transaction_cost"]
                        ),
                    }
                )

    fixed = pd.DataFrame(rows)

    # Add the stateful adaptive portfolio returns.
    adaptive = stateful.copy()
    adaptive = adaptive.loc[
        (adaptive["Date"] >= test_start)
        & (adaptive["Date"] <= test_end)
    ]

    adaptive = adaptive.rename(
        columns={
            "selected_rebalance_every": "selected_interval"
        }
    )
    adaptive["approach"] = "Adaptive walk-forward"

    adaptive = adaptive[
        [
            "Date",
            "strategy",
            "approach",
            "net_return",
            "gross_return",
            "turnover",
            "transaction_cost",
        ]
    ]

    combined = pd.concat(
        [fixed, adaptive],
        ignore_index=True,
    ).sort_values(["strategy", "approach", "Date"])

    if combined.duplicated(["strategy", "approach", "Date"]).any():
        raise ValueError("Duplicate strategy/approach/date records.")

    if combined["net_return"].isna().any():
        raise ValueError("Missing returns in comparison data.")

    summaries = []

    for (strategy_name, approach), group in combined.groupby(
        ["strategy", "approach"]
    ):
        group = group.sort_values("Date")
        metrics = calculate_performance_metrics(
            group["net_return"].reset_index(drop=True)
        )

        summaries.append(
            {
                "strategy": strategy_name,
                "approach": approach,
                "start_date": group["Date"].min().date().isoformat(),
                "end_date": group["Date"].max().date().isoformat(),
                "observations": len(group),
                "total_return": float(metrics["total_return"]),
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
                "total_turnover": float(group["turnover"].sum()),
                "total_transaction_cost_fraction": float(
                    group["transaction_cost"].sum()
                ),
            }
        )

    summary = pd.DataFrame(summaries).sort_values(
        ["strategy", "sharpe_ratio"],
        ascending=[True, False],
    )

    combined.to_csv(
        OUTPUT_DIR / "fixed_vs_adaptive_returns.csv",
        index=False,
    )
    summary.to_csv(
        OUTPUT_DIR / "fixed_vs_adaptive_summary.csv",
        index=False,
    )

    # Plot cumulative net returns for each strategy.
    for strategy_name, group in combined.groupby("strategy"):
        pivot = group.pivot(
            index="Date",
            columns="approach",
            values="net_return",
        ).sort_index()

        cumulative = (1 + pivot).cumprod()
        ax = cumulative.plot(figsize=(12, 6))
        ax.set_title(f"Fixed vs Adaptive Rebalancing — {strategy_name}")
        ax.set_xlabel("Date")
        ax.set_ylabel("Growth of 1 unit of capital")
        ax.grid(alpha=0.3)
        ax.legend(title="Approach")

        safe_name = (
            strategy_name.lower()
            .replace(" ", "_")
            .replace("/", "_")
        )
        plt.tight_layout()
        plt.savefig(
            OUTPUT_DIR / f"comparison_{safe_name}.png",
            dpi=160,
        )
        plt.close()

    print("=" * 76)
    print("FIXED VS ADAPTIVE WALK-FORWARD COMPARISON")
    print("=" * 76)
    print(f"Evaluation period: {test_start.date()} to {test_end.date()}")
    print(f"Transaction costs: {COST_BPS} bps")
    print()
    print(summary.to_string(
        index=False,
        float_format=lambda value: f"{value:.4f}",
    ))
    print()
    print(f"Saved comparison outputs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()