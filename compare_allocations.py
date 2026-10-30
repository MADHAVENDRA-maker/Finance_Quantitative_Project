from pathlib import Path

import pandas as pd

from backtest_allocations import load_asset_returns
from project_structure.features.performance import calculate_performance_metrics
from project_structure.features.relationships import calculate_covariance_matrix
from project_structure.portfolio.analytics import (
    calculate_portfolio_returns,
    calculate_portfolio_volatility,
)
from project_structure.portfolio.max_sharpe import calculate_maximum_sharpe_weights
from project_structure.portfolio.optimization import (
    calculate_equal_weights,
    calculate_minimum_variance_weights,
)

# Load aligned daily returns for every configured ETF.
asset_returns = load_asset_returns().dropna()

if asset_returns.empty:
    raise ValueError("No aligned return observations are available.")

print(f"Configured assets: {', '.join(asset_returns.columns)}")

# Estimate daily expected returns and daily covariance from this sample.
expected_daily_returns = asset_returns.mean()
daily_covariance = calculate_covariance_matrix(asset_returns)
daily_risk_free_rate = 0.0

allocations = {
    "Equal Weight": calculate_equal_weights(list(asset_returns.columns)),
    "Minimum Variance": calculate_minimum_variance_weights(daily_covariance),
    "Maximum Sharpe": calculate_maximum_sharpe_weights(
        expected_returns=expected_daily_returns,
        covariance=daily_covariance,
        risk_free_rate=daily_risk_free_rate,
    ),
}

print(f"Observations: {len(asset_returns)}")
print(
    f"Sample period: {asset_returns.index.min().date()} "
    f"to {asset_returns.index.max().date()}"
)

print("\nEstimated mean daily returns:")
print(expected_daily_returns.round(6).to_string())

print("\nPortfolio allocations:")
allocation_table = pd.DataFrame(allocations)
print((allocation_table * 100).round(2).astype(str).add("%").to_string())

# Evaluate each allocation over the same historical sample.
# Note: This is an in-sample comparison, not an out-of-sample backtest.
results = []

for name, weights in allocations.items():
    portfolio_returns = calculate_portfolio_returns(asset_returns, weights)
    metrics = calculate_performance_metrics(portfolio_returns)

    metrics["covariance_based_annualized_volatility"] = (
        calculate_portfolio_volatility(daily_covariance, weights)
    )

    metrics["mean_daily_return"] = float(portfolio_returns.mean())
    results.append(pd.Series(metrics, name=name))

comparison = pd.DataFrame(results)

print("\nIn-sample performance comparison:")
print(comparison.round(4).to_string())

# Save results for later analysis.
output_dir = load_asset_returns.__globals__.get(
    "PROJECT_ROOT", None
)

output_dir = Path(__file__).resolve().parent / "data" / "runs"
output_dir.mkdir(parents=True, exist_ok=True)

allocation_table.to_csv(output_dir / "portfolio_allocations.csv")
comparison.to_csv(output_dir / "portfolio_comparison.csv")

print("\nSaved:")
print(f"  {output_dir / 'portfolio_allocations.csv'}")
print(f"  {output_dir / 'portfolio_comparison.csv'}")