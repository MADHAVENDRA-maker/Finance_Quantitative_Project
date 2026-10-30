from itertools import product
from pathlib import Path

import pandas as pd

from backtest_allocations import LOOKBACK, STRATEGIES, load_asset_returns
from project_structure.backtesting.engine import run_backtest
from project_structure.features.performance import calculate_performance_metrics

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "runs" / "robustness"

REBALANCE_INTERVALS = (5, 21, 63)
TRANSACTION_COSTS_BPS = (0, 10, 25)


def run_robustness_analysis() -> pd.DataFrame:
    """Evaluate every strategy, cost, and rebalancing combination."""
    asset_returns = load_asset_returns()

    if len(asset_returns) <= LOOKBACK:
        raise ValueError(
            f"Need more than {LOOKBACK} return observations; "
            f"received {len(asset_returns)}."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    total_runs = (
        len(STRATEGIES)
        * len(REBALANCE_INTERVALS)
        * len(TRANSACTION_COSTS_BPS)
    )
    run_number = 0

    print("=" * 76)
    print("PORTFOLIO BACKTEST ROBUSTNESS ANALYSIS")
    print("=" * 76)
    print(f"Assets: {', '.join(asset_returns.columns)}")
    print(f"Lookback: {LOOKBACK} trading days")
    print(f"Rebalancing intervals: {REBALANCE_INTERVALS}")
    print(f"Transaction costs (bps): {TRANSACTION_COSTS_BPS}")
    print(f"Configurations: {total_runs}")
    print()

    for (
        (strategy_name, strategy),
        rebalance_every,
        cost_bps,
    ) in product(
        STRATEGIES.items(),
        REBALANCE_INTERVALS,
        TRANSACTION_COSTS_BPS,
    ):
        run_number += 1

        results = run_backtest(
            asset_returns=asset_returns,
            strategy=strategy,
            lookback=LOOKBACK,
            rebalance_every=rebalance_every,
            transaction_cost_bps=cost_bps,
        )

        metrics = {
            key: float(value)
            for key, value in calculate_performance_metrics(
                results["net_return"]
            ).items()
        }

        metrics.update(
            {
                "strategy": strategy_name,
                "lookback": LOOKBACK,
                "rebalance_every": rebalance_every,
                "transaction_cost_bps": cost_bps,
                "observations": len(results),
                "start_date": results.index.min().date().isoformat(),
                "end_date": results.index.max().date().isoformat(),
                "total_turnover": float(results["turnover"].sum()),
                "total_transaction_cost_fraction": float(
                    results["transaction_cost"].sum()
                ),
            }
        )

        rows.append(metrics)

        # Save each run independently for later inspection.
        filename = (
            f"{strategy_name.lower().replace(' ', '_')}"
            f"_rebalance_{rebalance_every}"
            f"_cost_{cost_bps}bps.csv"
        )
        results.to_csv(
            OUTPUT_DIR / filename,
            index_label="Date",
        )

        sharpe = metrics.get("sharpe_ratio", float("nan"))
        annual_return = metrics.get(
            "annualized_return", float("nan")
        )

        print(
            f"[{run_number:02d}/{total_runs}] "
            f"{strategy_name} | rebalance={rebalance_every} | "
            f"cost={cost_bps} bps | "
            f"annual return={annual_return:.2%} | "
            f"Sharpe={sharpe:.4f}"
        )

    summary = pd.DataFrame(rows)

    # Keep all 27 configurations in one comparison table.
    summary.to_csv(
        OUTPUT_DIR / "robustness_comparison.csv",
        index=False,
    )

    # Rank configurations by net Sharpe ratio.
    ranked = summary.sort_values(
        "sharpe_ratio",
        ascending=False,
    )
    ranked.to_csv(
        OUTPUT_DIR / "robustness_ranked_by_sharpe.csv",
        index=False,
    )

    # Show how results change with transaction costs for each
    # strategy and rebalancing interval.
    cost_sensitivity = summary.pivot(
        index=["strategy", "rebalance_every"],
        columns="transaction_cost_bps",
        values="sharpe_ratio",
    )
    cost_sensitivity.columns = [
        f"sharpe_at_{cost}_bps"
        for cost in cost_sensitivity.columns
    ]
    cost_sensitivity = cost_sensitivity.reset_index()
    cost_sensitivity.to_csv(
        OUTPUT_DIR / "transaction_cost_sensitivity.csv",
        index=False,
    )

    # Check whether every configuration uses the same OOS period.
    date_combinations = summary[
        ["start_date", "end_date", "observations"]
    ].drop_duplicates()

    print()
    print("=" * 76)
    print("TOP 10 CONFIGURATIONS BY NET SHARPE RATIO")
    print("=" * 76)
    print(
        ranked[
            [
                "strategy",
                "rebalance_every",
                "transaction_cost_bps",
                "annualized_return",
                "annualized_volatility",
                "sharpe_ratio",
                "maximum_drawdown",
                "total_turnover",
            ]
        ].head(10).to_string(index=False)
    )

    print()
    if len(date_combinations) == 1:
        print("PASS: All configurations use the same OOS period.")
    else:
        print(
            "WARNING: Configurations do not all share the same "
            "OOS period. Inspect robustness_comparison.csv."
        )
        print(date_combinations.to_string(index=False))

    print(f"\nAll robustness outputs saved to: {OUTPUT_DIR}")

    return summary


if __name__ == "__main__":
    run_robustness_analysis()