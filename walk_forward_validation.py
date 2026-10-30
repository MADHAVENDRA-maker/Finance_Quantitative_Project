from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from backtest_allocations import LOOKBACK, STRATEGIES, load_asset_returns
from project_structure.backtesting.engine import run_backtest
from project_structure.features.performance import calculate_performance_metrics

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "runs" / "walk_forward"

REBALANCE_INTERVALS = (5, 21, 63)
TRANSACTION_COST_BPS = 10.0
INITIAL_SELECTION_YEARS = 2


def normalize_datetime_index(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize index timestamps to a consistent, timezone-naive format."""
    frame = frame.copy()
    frame.index = pd.to_datetime(
        frame.index,
        errors="raise",
        utc=True,
    ).tz_localize(None)
    return frame.sort_index()


def calculate_sharpe(returns: pd.Series) -> float:
    """Calculate annualized daily-return Sharpe ratio, assuming zero risk-free rate."""
    returns = returns.dropna()

    if len(returns) < 2:
        return float("nan")

    volatility = returns.std(ddof=1)

    if not np.isfinite(volatility) or volatility == 0:
        return float("nan")

    return float(np.sqrt(252) * returns.mean() / volatility)


def validate_candidate_runs(
    candidate_runs: dict,
) -> None:
    """Check that candidate backtests have consistent, valid output."""
    if not candidate_runs:
        raise ValueError("No candidate backtests were generated.")

    reference_index = None

    for key, frame in candidate_runs.items():
        if frame.empty:
            raise ValueError(f"Empty backtest result for {key}.")

        if "net_return" not in frame.columns:
            raise ValueError(f"Missing net_return column for {key}.")

        values = frame["net_return"].to_numpy(dtype=float)

        if not np.isfinite(values).all() or (values < -1.0).any():
            raise ValueError(f"Invalid net returns for {key}.")

        if not frame.index.is_unique:
            raise ValueError(f"Duplicate dates found for {key}.")

        if reference_index is None:
            reference_index = frame.index
        elif not frame.index.equals(reference_index):
            raise ValueError(
                "Candidate backtests have inconsistent dates. "
                f"First mismatch encountered for {key}."
            )


def generate_candidate_runs(
    asset_returns: pd.DataFrame,
) -> dict:
    """Run each strategy at each candidate rebalancing interval."""
    candidate_runs = {}

    for strategy_name, strategy_function in STRATEGIES.items():
        for interval in REBALANCE_INTERVALS:
            key = (strategy_name, interval)

            result = run_backtest(
                asset_returns=asset_returns,
                strategy=strategy_function,
                lookback=LOOKBACK,
                rebalance_every=interval,
                transaction_cost_bps=TRANSACTION_COST_BPS,
            )

            result = normalize_datetime_index(result)
            candidate_runs[key] = result

            print(
                f"Generated: {strategy_name} | "
                f"rebalance={interval} days | "
                f"observations={len(result)}"
            )

    validate_candidate_runs(candidate_runs)
    return candidate_runs


def select_rebalance_interval(
    strategy_name: str,
    candidate_runs: dict,
    test_year: int,
) -> tuple[int, float, int]:
    """Select a rebalance interval using only returns before test_year."""
    historical_scores = []

    for interval in REBALANCE_INTERVALS:
        frame = candidate_runs[(strategy_name, interval)]

        historical = frame.loc[
            frame.index.year < test_year,
            "net_return",
        ]

        score = calculate_sharpe(historical)

        if np.isfinite(score):
            historical_scores.append(
                (interval, score, len(historical))
            )

    if not historical_scores:
        raise ValueError(
            f"Insufficient historical returns to select a configuration "
            f"for {strategy_name} in {test_year}."
        )

    # Deterministic tie-break: prefer less frequent rebalancing.
    selected_interval, selected_score, observations = max(
        historical_scores,
        key=lambda item: (item[1], item[0]),
    )

    return selected_interval, selected_score, observations


def run_walk_forward(
    candidate_runs: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Select settings from past returns and evaluate the next calendar year."""
    reference_frame = next(iter(candidate_runs.values()))
    available_years = sorted(reference_frame.index.year.unique())

    if len(available_years) <= INITIAL_SELECTION_YEARS:
        raise ValueError(
            "Not enough calendar years for walk-forward evaluation. "
            f"Available years: {available_years}"
        )

    decision_rows = []
    return_rows = []

    test_years = available_years[INITIAL_SELECTION_YEARS:]

    for test_year in test_years:
        for strategy_name in STRATEGIES:
            interval, selection_score, history_count = (
                select_rebalance_interval(
                    strategy_name,
                    candidate_runs,
                    test_year,
                )
            )

            selected_frame = candidate_runs[
                (strategy_name, interval)
            ]

            test_frame = selected_frame.loc[
                selected_frame.index.year == test_year
            ]

            if test_frame.empty:
                continue

            decision_rows.append(
                {
                    "strategy": strategy_name,
                    "test_year": int(test_year),
                    "selected_rebalance_every": interval,
                    "transaction_cost_bps": TRANSACTION_COST_BPS,
                    "selection_sharpe": selection_score,
                    "selection_observations": history_count,
                    "selection_start": (
                        selected_frame.index[
                            selected_frame.index.year < test_year
                        ].min().date().isoformat()
                    ),
                    "selection_end": (
                        selected_frame.index[
                            selected_frame.index.year < test_year
                        ].max().date().isoformat()
                    ),
                    "test_start": test_frame.index.min().date().isoformat(),
                    "test_end": test_frame.index.max().date().isoformat(),
                    "test_observations": len(test_frame),
                }
            )

            for date, row in test_frame.iterrows():
                return_rows.append(
                    {
                        "Date": date,
                        "strategy": strategy_name,
                        "selected_rebalance_every": interval,
                        "net_return": float(row["net_return"]),
                        "turnover": float(row["turnover"]),
                    }
                )

    decisions = pd.DataFrame(decision_rows)
    out_of_sample_returns = pd.DataFrame(return_rows)

    if decisions.empty or out_of_sample_returns.empty:
        raise ValueError("Walk-forward evaluation produced no test results.")

    return decisions, out_of_sample_returns


def summarize_results(
    out_of_sample_returns: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize the concatenated yearly test returns for each strategy."""
    rows = []

    for strategy_name, group in out_of_sample_returns.groupby("strategy"):
        group = group.sort_values("Date")
        returns = group["net_return"].reset_index(drop=True)

        metrics = calculate_performance_metrics(returns)

        rows.append(
            {
                "strategy": strategy_name,
                "test_start": group["Date"].min().date().isoformat(),
                "test_end": group["Date"].max().date().isoformat(),
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
                "average_daily_turnover": float(
                    group["turnover"].mean()
                ),
            }
        )

    return pd.DataFrame(rows).sort_values(
        "sharpe_ratio",
        ascending=False,
    )


def plot_cumulative_returns(
    out_of_sample_returns: pd.DataFrame,
) -> None:
    """Plot cumulative wealth from the selected yearly test returns."""
    pivot = out_of_sample_returns.pivot(
        index="Date",
        columns="strategy",
        values="net_return",
    ).sort_index()

    cumulative = (1.0 + pivot.fillna(0.0)).cumprod()

    ax = cumulative.plot(figsize=(12, 6))
    ax.set_title("Walk-Forward Out-of-Sample Cumulative Returns")
    ax.set_xlabel("Date")
    ax.set_ylabel("Growth of 1 unit of capital")
    ax.grid(alpha=0.3)
    ax.legend(title="Strategy")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "walk_forward_cumulative_returns.png",
        dpi=160,
    )
    plt.close()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    asset_returns = load_asset_returns()
    asset_returns = normalize_datetime_index(asset_returns)

    if asset_returns.isna().any().any():
        raise ValueError(
            "Asset returns contain missing values. "
            "Resolve them before running the evaluation."
        )

    print("=" * 76)
    print("EXPANDING-WINDOW WALK-FORWARD VALIDATION")
    print("=" * 76)
    print(f"Input observations: {len(asset_returns)}")
    print(f"Input start: {asset_returns.index.min().date()}")
    print(f"Input end: {asset_returns.index.max().date()}")
    print(f"Assets: {list(asset_returns.columns)}")
    print(f"Lookback: {LOOKBACK} trading days")
    print(f"Transaction costs: {TRANSACTION_COST_BPS} bps")
    print(f"Candidate intervals: {REBALANCE_INTERVALS}")
    print(
        f"Initial selection history: "
        f"{INITIAL_SELECTION_YEARS} calendar years"
    )
    print()

    candidate_runs = generate_candidate_runs(asset_returns)

    decisions, test_returns = run_walk_forward(candidate_runs)
    summary = summarize_results(test_returns)

    decisions.to_csv(
        OUTPUT_DIR / "walk_forward_decisions.csv",
        index=False,
    )
    test_returns.to_csv(
        OUTPUT_DIR / "walk_forward_returns.csv",
        index=False,
    )
    summary.to_csv(
        OUTPUT_DIR / "walk_forward_summary.csv",
        index=False,
    )

    plot_cumulative_returns(test_returns)

    print()
    print("WALK-FORWARD SUMMARY")
    print(
        summary.to_string(
            index=False,
            float_format=lambda value: f"{value:.4f}",
        )
    )

    print()
    print("YEARLY CONFIGURATION DECISIONS")
    print(
        decisions[
            [
                "strategy",
                "test_year",
                "selected_rebalance_every",
                "selection_sharpe",
                "selection_observations",
                "test_observations",
            ]
        ].to_string(
            index=False,
            float_format=lambda value: f"{value:.4f}",
        )
    )

    print()
    print("Output directory:")
    print(OUTPUT_DIR)
    print("- walk_forward_decisions.csv")
    print("- walk_forward_returns.csv")
    print("- walk_forward_summary.csv")
    print("- walk_forward_cumulative_returns.png")


if __name__ == "__main__":
    main()