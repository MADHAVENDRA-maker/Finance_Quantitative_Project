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
OUTPUT_DIR = PROJECT_ROOT / "data" / "runs" / "walk_forward_stateful"

REBALANCE_INTERVALS = (5, 21, 63)
TRANSACTION_COST_BPS = 10.0
INITIAL_SELECTION_YEARS = 2
TRADING_DAYS_PER_YEAR = 252


def normalize_index(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert timestamps to a sorted, timezone-naive DatetimeIndex."""
    frame = frame.copy()
    frame.index = pd.to_datetime(
        frame.index, errors="raise", utc=True
    ).tz_localize(None)
    return frame.sort_index()


def sharpe_ratio(returns: pd.Series) -> float:
    """Annualized Sharpe ratio assuming a zero risk-free rate."""
    values = returns.dropna().to_numpy(dtype=float)

    if len(values) < 2:
        return float("nan")

    daily_volatility = np.std(values, ddof=1)

    if not np.isfinite(daily_volatility) or daily_volatility == 0:
        return float("nan")

    return float(
        np.sqrt(TRADING_DAYS_PER_YEAR)
        * np.mean(values)
        / daily_volatility
    )


def validate_weights(
    weights: pd.Series,
    asset_names: list[str],
) -> pd.Series:
    """Validate and align a strategy's target weights."""
    if not isinstance(weights, pd.Series):
        weights = pd.Series(weights, index=asset_names, dtype=float)

    weights = weights.reindex(asset_names).astype(float)

    if weights.isna().any() or not np.isfinite(weights.to_numpy()).all():
        raise ValueError("Target weights contain missing or non-finite values.")

    if (weights < -1e-8).any():
        raise ValueError("Negative target weights are not supported.")

    if not np.isclose(weights.sum(), 1.0, atol=1e-6):
        raise ValueError(
            f"Target weights must sum to 1; received {weights.sum():.8f}."
        )

    # Remove negligible numerical noise.
    weights = weights.clip(lower=0.0)
    return weights / weights.sum()


def build_candidate_backtests(
    asset_returns: pd.DataFrame,
) -> dict[tuple[str, int], pd.DataFrame]:
    """Run existing backtests to obtain historical selection scores."""
    candidates = {}

    for strategy_name, strategy_function in STRATEGIES.items():
        for interval in REBALANCE_INTERVALS:
            result = run_backtest(
                asset_returns=asset_returns,
                strategy=strategy_function,
                lookback=LOOKBACK,
                rebalance_every=interval,
                transaction_cost_bps=TRANSACTION_COST_BPS,
            )
            result = normalize_index(result)
            candidates[(strategy_name, interval)] = result

    reference_index = next(iter(candidates.values())).index

    for key, frame in candidates.items():
        if not frame.index.equals(reference_index):
            raise ValueError(
                f"Candidate backtest dates differ for {key}."
            )

        if frame["net_return"].isna().any():
            raise ValueError(
                f"Missing net returns in candidate backtest {key}."
            )

    return candidates


def select_interval(
    strategy_name: str,
    test_year: int,
    candidates: dict[tuple[str, int], pd.DataFrame],
) -> dict:
    """Select an interval using candidate returns strictly before test_year."""
    scores = []

    for interval in REBALANCE_INTERVALS:
        frame = candidates[(strategy_name, interval)]

        history = frame.loc[
            frame.index.year < test_year,
            "net_return",
        ]

        score = sharpe_ratio(history)

        if np.isfinite(score):
            scores.append(
                {
                    "interval": interval,
                    "score": score,
                    "observations": len(history),
                }
            )

    if not scores:
        raise ValueError(
            f"No valid selection history for {strategy_name}, {test_year}."
        )

    # If scores tie, prefer the longer interval to reduce trading.
    selected = max(
        scores,
        key=lambda item: (item["score"], item["interval"]),
    )

    return selected


def make_yearly_decisions(
    candidates: dict[tuple[str, int], pd.DataFrame],
) -> pd.DataFrame:
    """Record the interval selected for each strategy and test year."""
    reference = next(iter(candidates.values()))
    years = sorted(reference.index.year.unique())

    if len(years) <= INITIAL_SELECTION_YEARS:
        raise ValueError("Insufficient years for walk-forward evaluation.")

    rows = []

    for test_year in years[INITIAL_SELECTION_YEARS:]:
        for strategy_name in STRATEGIES:
            selected = select_interval(
                strategy_name,
                int(test_year),
                candidates,
            )

            rows.append(
                {
                    "strategy": strategy_name,
                    "test_year": int(test_year),
                    "selected_rebalance_every": selected["interval"],
                    "selection_sharpe": selected["score"],
                    "selection_observations": selected["observations"],
                    "transaction_cost_bps": TRANSACTION_COST_BPS,
                }
            )

    return pd.DataFrame(rows)


def simulate_stateful_portfolio(
    asset_returns: pd.DataFrame,
    strategy_name: str,
    strategy_function,
    decisions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Simulate a continuous portfolio and record weights at each stage.

    Weight columns:
    - target_weight_<asset>: strategy target on rebalance dates; NaN otherwise.
    - applied_weight_<asset>: holdings used to calculate that day's gross return.
    - weight_<asset>: drifted holdings after that day's asset returns.

    Turnover uses the full L1 distance between target weights and
    pre-trade drifted weights. The initial allocation is treated as a
    trade from cash, so initial turnover is 1.0.
    """
    strategy_decisions = decisions.loc[
        decisions["strategy"] == strategy_name
    ]

    if strategy_decisions.empty:
        raise ValueError(
            f"No yearly decisions found for strategy {strategy_name}."
        )

    if strategy_decisions["test_year"].duplicated().any():
        raise ValueError(
            f"Duplicate yearly decisions for strategy {strategy_name}."
        )

    decision_map = (
        strategy_decisions
        .set_index("test_year")["selected_rebalance_every"]
        .to_dict()
    )

    for year, interval in decision_map.items():
        if int(interval) not in REBALANCE_INTERVALS:
            raise ValueError(
                f"Invalid rebalance interval {interval} for {year}."
            )

    first_test_year = min(decision_map)
    asset_names = list(asset_returns.columns)
    asset_values = asset_returns.to_numpy(dtype=float)

    if not asset_returns.index.is_unique:
        raise ValueError("Asset return index contains duplicate dates.")

    if not asset_returns.index.is_monotonic_increasing:
        raise ValueError("Asset return dates must be sorted.")

    if asset_returns.isna().any().any():
        raise ValueError("Asset returns contain missing values.")

    if not np.isfinite(asset_values).all():
        raise ValueError("Asset returns contain non-finite values.")

    if (asset_values < -1.0).any():
        raise ValueError("Asset returns cannot be less than -100%.")

    if LOOKBACK < 1:
        raise ValueError("LOOKBACK must be at least one trading day.")

    if len(asset_returns) <= LOOKBACK:
        raise ValueError("Insufficient data for the specified lookback.")

    if TRANSACTION_COST_BPS < 0:
        raise ValueError("Transaction costs cannot be negative.")

    # Start in cash, matching the existing engine's initial-turnover
    # convention. The first allocation is made at the first eligible date.
    actual_weights = pd.Series(
        0.0, index=asset_names, dtype=float
    )
    last_rebalance_position = None
    current_interval = 21
    rows = []

    for i in range(LOOKBACK, len(asset_returns)):
        date = asset_returns.index[i]
        year = int(date.year)

        # During initialization, use a fixed 21-day schedule.
        # After selection starts, use the interval chosen for this year.
        interval = (
            int(decision_map[year])
            if year >= first_test_year and year in decision_map
            else 21
        )

        interval_changed = interval != current_interval

        rebalance_due = (
            last_rebalance_position is None
            or interval_changed
            or i - last_rebalance_position >= interval
        )

        # Record weights immediately before the possible rebalance.
        pre_trade_weights = actual_weights.copy()

        if rebalance_due:
            history = asset_returns.iloc[i - LOOKBACK:i]

            target_weights = validate_weights(
                strategy_function(history),
                asset_names,
            )

            turnover = float(
                (target_weights - pre_trade_weights).abs().sum()
            )

            # Target and applied weights coincide at execution.
            applied_weights = target_weights.copy()

            last_rebalance_position = i
            current_interval = interval
        else:
            # No trade: existing holdings have drifted since the previous
            # close and remain the holdings used for today's return.
            target_weights = pd.Series(
                np.nan, index=asset_names, dtype=float
            )
            applied_weights = pre_trade_weights.copy()
            turnover = 0.0

        daily_asset_returns = pd.Series(
            asset_values[i],
            index=asset_names,
            dtype=float,
        )

        gross_return = float(
            (applied_weights * daily_asset_returns).sum()
        )

        if gross_return <= -1.0:
            raise ValueError(
                f"Portfolio value reached zero or below on {date.date()}."
            )

        # Turnover is the full L1 distance. Costs are charged as a fraction
        # of pre-trade portfolio value, as in the existing implementation.
        cost_fraction = (
            turnover * TRANSACTION_COST_BPS / 10_000.0
        )

        net_return = (
            (1.0 - cost_fraction) * (1.0 + gross_return) - 1.0
        )

        # Holdings after asset returns, before the next rebalance.
        drifted_weights = (
            applied_weights * (1.0 + daily_asset_returns)
            / (1.0 + gross_return)
        )

        drifted_total = float(drifted_weights.sum())

        if (
            not np.isfinite(drifted_total)
            or drifted_total <= 0
        ):
            raise ValueError(
                f"Invalid drifted weights on {date.date()}."
            )

        drifted_weights = drifted_weights / drifted_total

        # Continue portfolio accounting during initialization, but only
        # emit rows for the shared evaluation period.
        if year >= first_test_year:
            row = {
                "Date": date,
                "strategy": strategy_name,
                "selected_rebalance_every": interval,
                "rebalanced": bool(rebalance_due),
                "interval_changed": bool(interval_changed),
                "gross_return": gross_return,
                "net_return": net_return,
                "turnover": turnover,
                "transaction_cost": cost_fraction,
                "transaction_cost_bps": TRANSACTION_COST_BPS,
            }

            for asset in asset_names:
                # Only populated when a strategy target is generated.
                row[f"target_weight_{asset}"] = float(
                    target_weights[asset]
                )

                # Portfolio weights used to generate today's gross return.
                row[f"applied_weight_{asset}"] = float(
                    applied_weights[asset]
                )

                # Portfolio weights after today's asset returns.
                # Keep the original "weight_<asset>" names for compatibility.
                row[f"weight_{asset}"] = float(
                    drifted_weights[asset]
                )

            rows.append(row)

        # Carry drifted holdings forward to the next trading date.
        actual_weights = drifted_weights

    result = pd.DataFrame(rows)

    if result.empty:
        raise ValueError(
            f"No evaluation-period returns for {strategy_name}."
        )

    if result["Date"].duplicated().any():
        raise ValueError(
            f"Duplicate output dates for {strategy_name}."
        )

    if not np.isfinite(result["net_return"].to_numpy()).all():
        raise ValueError(
            f"Non-finite net returns for {strategy_name}."
        )

    if not np.isfinite(result["gross_return"].to_numpy()).all():
        raise ValueError(
            f"Non-finite gross returns for {strategy_name}."
        )

    if (result["turnover"] < 0).any():
        raise ValueError("Turnover cannot be negative.")

    if (result["transaction_cost"] < 0).any():
        raise ValueError("Transaction costs cannot be negative.")

    # Every applied and drifted weight vector must sum to one.
    applied_columns = [
        f"applied_weight_{asset}" for asset in asset_names
    ]
    drifted_columns = [
        f"weight_{asset}" for asset in asset_names
    ]

    if not np.allclose(
        result[applied_columns].sum(axis=1),
        1.0,
        atol=1e-8,
    ):
        raise ValueError("Applied portfolio weights do not sum to one.")

    if not np.allclose(
        result[drifted_columns].sum(axis=1),
        1.0,
        atol=1e-8,
    ):
        raise ValueError("Drifted portfolio weights do not sum to one.")

    # Non-rebalance rows must have no target weights recorded.
    target_columns = [
        f"target_weight_{asset}" for asset in asset_names
    ]
    no_rebalance = ~result["rebalanced"]

    if result.loc[no_rebalance, target_columns].notna().any().any():
        raise ValueError(
            "Target weights should be missing on non-rebalance dates."
        )

    return result


def summarize_portfolios(
    results: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate performance metrics from the stateful test returns."""
    summaries = []

    for strategy_name, group in results.groupby("strategy"):
        group = group.sort_values("Date")
        returns = group["net_return"].reset_index(drop=True)

        metrics = calculate_performance_metrics(returns)

        summaries.append(
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
                "rebalance_count": int(group["rebalanced"].sum()),
                "total_turnover": float(group["turnover"].sum()),
                "total_transaction_cost_fraction": float(
                    group["transaction_cost"].sum()
                ),
            }
        )

    return pd.DataFrame(summaries).sort_values(
        "sharpe_ratio", ascending=False
    )


def plot_cumulative_returns(results: pd.DataFrame) -> None:
    """Plot continuous cumulative net returns for each strategy."""
    pivot = results.pivot(
        index="Date",
        columns="strategy",
        values="net_return",
    ).sort_index()

    cumulative = (1.0 + pivot).cumprod()

    ax = cumulative.plot(figsize=(12, 6))
    ax.set_title("Stateful Walk-Forward Cumulative Returns")
    ax.set_xlabel("Date")
    ax.set_ylabel("Growth of 1 unit of capital")
    ax.grid(alpha=0.3)
    ax.legend(title="Strategy")

    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "stateful_walk_forward_cumulative_returns.png",
        dpi=160,
    )
    plt.close()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    asset_returns = normalize_index(load_asset_returns())

    if asset_returns.isna().any().any():
        raise ValueError("Asset return input contains missing values.")

    if not asset_returns.index.is_unique:
        raise ValueError("Asset return input contains duplicate dates.")

    print("=" * 76)
    print("STATEFUL WALK-FORWARD VALIDATION")
    print("=" * 76)
    print(f"Assets: {list(asset_returns.columns)}")
    print(
        f"Input period: {asset_returns.index.min().date()} to "
        f"{asset_returns.index.max().date()}"
    )
    print(f"Lookback: {LOOKBACK} trading days")
    print(f"Candidate intervals: {REBALANCE_INTERVALS}")
    print(f"Transaction costs: {TRANSACTION_COST_BPS} bps")
    print()

    candidates = build_candidate_backtests(asset_returns)
    decisions = make_yearly_decisions(candidates)

    stateful_results = []

    for strategy_name, strategy_function in STRATEGIES.items():
        print(f"Simulating stateful portfolio: {strategy_name}")

        strategy_results = simulate_stateful_portfolio(
            asset_returns=asset_returns,
            strategy_name=strategy_name,
            strategy_function=strategy_function,
            decisions=decisions,
        )

        stateful_results.append(strategy_results)

    results = pd.concat(stateful_results, ignore_index=True)
    results = results.sort_values(["strategy", "Date"])

    summary = summarize_portfolios(results)

    # Confirm all strategies cover identical test dates.
    date_sets = {
        name: set(group["Date"])
        for name, group in results.groupby("strategy")
    }

    if len({frozenset(dates) for dates in date_sets.values()}) != 1:
        raise ValueError(
            "Strategies do not cover the same test dates."
        )

    decisions.to_csv(
        OUTPUT_DIR / "stateful_walk_forward_decisions.csv",
        index=False,
    )
    results.to_csv(
        OUTPUT_DIR / "stateful_walk_forward_returns.csv",
        index=False,
    )
    summary.to_csv(
        OUTPUT_DIR / "stateful_walk_forward_summary.csv",
        index=False,
    )

    plot_cumulative_returns(results)

    print()
    print("STATEFUL WALK-FORWARD SUMMARY")
    print(
        summary.to_string(
            index=False,
            float_format=lambda value: f"{value:.4f}",
        )
    )

    print()
    print("YEARLY CONFIGURATION DECISIONS")
    print(
        decisions.to_string(
            index=False,
            float_format=lambda value: f"{value:.4f}",
        )
    )

    print()
    print("Output directory:")
    print(OUTPUT_DIR)
    print("- stateful_walk_forward_decisions.csv")
    print("- stateful_walk_forward_returns.csv")
    print("- stateful_walk_forward_summary.csv")
    print("- stateful_walk_forward_cumulative_returns.png")


if __name__ == "__main__":
    main()