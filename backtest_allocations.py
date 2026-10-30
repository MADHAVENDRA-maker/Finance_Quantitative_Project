from pathlib import Path

import pandas as pd

from project_structure.backtesting.engine import run_backtest
from project_structure.backtesting.strategies import (
    equal_weight_strategy,
    maximum_sharpe_strategy,
    minimum_variance_strategy,
)
from project_structure.config import load_assets_config
from project_structure.data.returns import calculate_universe_returns
from project_structure.features.performance import calculate_performance_metrics

PROJECT_ROOT = Path(__file__).resolve().parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNS_DIR = PROJECT_ROOT / "data" / "runs"

LOOKBACK = 252
REBALANCE_EVERY = 21
TRANSACTION_COST_BPS = 10

STRATEGIES = {
    "Equal Weight": equal_weight_strategy,
    "Minimum Variance": minimum_variance_strategy,
    "Maximum Sharpe": maximum_sharpe_strategy,
}


def load_asset_returns() -> pd.DataFrame:
    """Load configured asset histories and calculate aligned daily returns."""
    assets_config = load_assets_config()
    tickers = [asset.ticker for asset in assets_config.assets]

    if not tickers:
        raise ValueError("No assets are configured in configs/assets.yaml.")

    price_files = {}

    for ticker in tickers:
        path = PROCESSED_DIR / f"{ticker}.csv"

        if not path.exists():
            raise FileNotFoundError(
                f"Processed data for configured asset {ticker} not found: {path}"
            )

        prices = pd.read_csv(
            path,
            index_col="Date",
            parse_dates=True,
        )

        if prices.empty:
            raise ValueError(f"Processed price data for {ticker} is empty.")

        if not prices.index.is_monotonic_increasing:
            prices = prices.sort_index()

        if prices.index.has_duplicates:
            raise ValueError(
                f"Processed price data for {ticker} contains duplicate dates."
            )

        price_files[ticker] = prices

    returns = calculate_universe_returns(price_files).dropna()
    returns = returns.sort_index()

    if returns.empty:
        raise ValueError("No aligned asset returns are available.")

    return returns


def main() -> None:
    """Run strategies, save their results, and compare performance."""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    asset_returns = load_asset_returns()

    if len(asset_returns) <= LOOKBACK:
        raise ValueError(
            f"Need more than {LOOKBACK} return observations; "
            f"received {len(asset_returns)}."
        )

    print("=" * 72)
    print("OUT-OF-SAMPLE PORTFOLIO BACKTEST")
    print("=" * 72)
    print(f"Assets: {', '.join(asset_returns.columns)}")
    print(f"Available return observations: {len(asset_returns)}")
    print(f"Available period: {asset_returns.index.min().date()} "
          f"to {asset_returns.index.max().date()}")
    print(f"Lookback: {LOOKBACK} trading days")
    print(f"Rebalancing interval: {REBALANCE_EVERY} trading days")
    print(f"Transaction costs: {TRANSACTION_COST_BPS} bps")
    print()

    comparison_rows = []

    for name, strategy in STRATEGIES.items():
        results = run_backtest(
            asset_returns=asset_returns,
            strategy=strategy,
            lookback=LOOKBACK,
            rebalance_every=REBALANCE_EVERY,
            transaction_cost_bps=TRANSACTION_COST_BPS,
        )

        metrics = calculate_performance_metrics(results["net_return"])

        metrics = {
            key: float(value)
            for key, value in metrics.items()
        }

        metrics["strategy"] = name
        metrics["observations"] = len(results)
        metrics["start_date"] = results.index.min().date().isoformat()
        metrics["end_date"] = results.index.max().date().isoformat()
        metrics["total_turnover"] = float(results["turnover"].sum())
        metrics["total_transaction_cost"] = float(
            results["transaction_cost"].sum()
        )

        results["cumulative_gross_return"] = (
            1.0 + results["gross_return"]
        ).cumprod() - 1.0

        results["cumulative_net_return"] = (
            1.0 + results["net_return"]
        ).cumprod() - 1.0

        filename = name.lower().replace(" ", "_")
        output_path = RUNS_DIR / f"backtest_{filename}.csv"
        results.to_csv(output_path, index_label="Date")

        comparison_rows.append(metrics)

        print(f"Strategy: {name}")
        print(f"Out-of-sample period: {metrics['start_date']} "
              f"to {metrics['end_date']}")
        print(f"Observations: {metrics['observations']}")
        print(f"Total return: {metrics.get('total_return', float('nan')):.2%}")
        print(
            "Annualized return: "
            f"{metrics.get('annualized_return', float('nan')):.2%}"
        )
        print(
            "Annualized volatility: "
            f"{metrics.get('annualized_volatility', float('nan')):.2%}"
        )
        print(
            f"Sharpe ratio: {metrics.get('sharpe_ratio', float('nan')):.4f}"
        )
        print(
            "Maximum drawdown: "
            f"{metrics.get('maximum_drawdown', float('nan')):.2%}"
        )
        print(f"Total L1 turnover: {metrics['total_turnover']:.4f}")
        print(
            "Sum of transaction-cost fractions: "
            f"{metrics['total_transaction_cost']:.4%}"
        )
        print(f"Saved results: {output_path}")
        print("-" * 72)

    comparison = pd.DataFrame(comparison_rows).set_index("strategy")
    comparison_path = RUNS_DIR / "backtest_comparison.csv"
    comparison.to_csv(comparison_path, index_label="strategy")

    print("\nCOMPARISON TABLE")
    print(comparison.to_string())
    print(f"\nSaved comparison: {comparison_path}")


if __name__ == "__main__":
    main()