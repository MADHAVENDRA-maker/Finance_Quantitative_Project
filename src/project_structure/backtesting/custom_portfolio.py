from collections.abc import Mapping
import numpy as np
import pandas as pd
from project_structure.backtesting.engine import run_backtest
from project_structure.features.performance import (calculate_performance_metrics)
from project_structure.portfolio.analytics import validate_portfolio_weights

def run_custom_portfolio_backtest(
    asset_returns: pd.DataFrame,
    weights: Mapping[str, float] | pd.Series,
    lookback: int = 252,
    rebalance_every: int = 21,
    transaction_cost_bps: float = 10.0,
) -> tuple[pd.DataFrame, dict[str, float], pd.Series]:
    """Backtest a fixed-target-weight portfolio out of sample.

    Target weights are restored only at scheduled rebalances. Holdings
    drift between rebalances, and transaction costs are charged by the
    existing backtest engine.

    Returns:
        results: Backtest series, including net returns and applied weights.
        metrics: Performance and trading metrics calculated from the results.
        drawdown: Net-wealth drawdown series.
    """
    if not isinstance(asset_returns, pd.DataFrame):
        raise TypeError("asset_returns must be a pandas DataFrame.")

    if asset_returns.empty or asset_returns.shape[1] == 0:
        raise ValueError("asset_returns must contain assets and observations.")

    if asset_returns.columns.has_duplicates:
        raise ValueError("Asset return columns must be unique.")

    if not isinstance(weights, (Mapping, pd.Series)):
        raise TypeError("weights must be a mapping or pandas Series.")

    target_weights = validate_portfolio_weights(weights)

    if set(target_weights.index) != set(asset_returns.columns):
        raise ValueError(
            "Selected return columns must match the portfolio weight assets."
        )

    # Keep the order consistent with the supplied return DataFrame.
    target_weights = target_weights.reindex(asset_returns.columns)

    def fixed_weight_strategy(history: pd.DataFrame) -> pd.Series:
        # The engine supplies only the trailing, pre-evaluation history.
        # Fixed target weights intentionally do not depend on future data.
        return target_weights.copy()

    results = run_backtest(
        asset_returns=asset_returns,
        strategy=fixed_weight_strategy,
        lookback=lookback,
        rebalance_every=rebalance_every,
        transaction_cost_bps=transaction_cost_bps,
    )

    net_returns = results["net_return"]
    metrics = calculate_performance_metrics(net_returns)

    wealth = (1.0 + net_returns).cumprod()
    running_peak = wealth.cummax().clip(lower=1.0)
    drawdown = wealth / running_peak - 1.0
    drawdown.name = "drawdown"

    metrics.update(
        {
            "observations": int(len(results)),
            "start_date": str(results.index.min().date()),
            "end_date": str(results.index.max().date()),
            "average_turnover": float(results["turnover"].mean()),
            "total_turnover": float(results["turnover"].sum()),
            "total_transaction_cost": float(
                results["transaction_cost"].sum()
            ),
        }
    )

    return results, metrics, drawdown