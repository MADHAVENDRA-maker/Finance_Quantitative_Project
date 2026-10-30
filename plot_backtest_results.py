from pathlib import Path

import pandas as pd

from project_structure.backtesting.visualization import (
    plot_allocation_weights,
    plot_cumulative_returns,
    plot_drawdowns,
    plot_rolling_sharpe,
    plot_rolling_volatility,
    plot_strategy_turnover,
)

PROJECT_ROOT = Path(__file__).resolve().parent
RUNS_DIR = PROJECT_ROOT / "data" / "runs"

FILES = {
    "Equal Weight": "backtest_equal_weight.csv",
    "Minimum Variance": "backtest_minimum_variance.csv",
    "Maximum Sharpe": "backtest_maximum_sharpe.csv",
}


def main() -> None:
    results = {}

    for strategy_name, filename in FILES.items():
        path = RUNS_DIR / filename

        if not path.exists():
            raise FileNotFoundError(
                f"Backtest results not found: {path}. "
                "Run backtest_allocations.py first."
            )

        frame = pd.read_csv(path, index_col="Date", parse_dates=True)
        results[strategy_name] = frame.sort_index()

    cumulative_path = plot_cumulative_returns(results, RUNS_DIR)
    drawdown_path = plot_drawdowns(results, RUNS_DIR)
    sharpe_path = plot_rolling_sharpe(results,RUNS_DIR,window=63,risk_free_rate=0.0)
    volatility_path = plot_rolling_volatility(results,RUNS_DIR,window=63)
    allocation_path = plot_allocation_weights(results, RUNS_DIR)
    turnover_path = plot_strategy_turnover(results, RUNS_DIR)

    print("Backtest visualizations generated successfully.")
    print(f"Cumulative returns: {cumulative_path}")
    print(f"Drawdowns: {drawdown_path}")
    print(f"Rolling Sharpe ratio: {sharpe_path}")
    print(f"Rolling volatility: {volatility_path}")
    print(f"Allocation weights: {allocation_path}")
    print(f"Strategy turnover: {turnover_path}")


if __name__ == "__main__":
    main()