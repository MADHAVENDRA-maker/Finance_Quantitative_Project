# Maximum-Sharpe Portfolio Optimization

## Objective

This stage extends the portfolio optimization module with a long-only maximum-Sharpe strategy. It complements the existing equal-weight and minimum-variance allocations.

## Methodology

The `calculate_maximum_sharpe_weights()` function seeks to maximize the portfolio's estimated excess return per unit of volatility.

Inputs:
- Expected periodic returns for each asset
- A periodic covariance matrix
- A risk-free rate expressed at the same frequency

Constraints:
- Each asset weight lies between 0 and 1.
- All portfolio weights sum to 1.
- Expected returns and covariance must be finite and correctly labelled.
- The covariance matrix must be symmetric and positive semidefinite.

The optimizer uses SciPy's SLSQP solver with multiple starting allocations to improve robustness.

## Historical comparison

The strategy was evaluated using SPY and TLT daily returns from January 3, 2020, to October 23, 2026, with 1,711 aligned observations.

| Metric | Equal weight | Minimum variance | Maximum Sharpe |
|---|---:|---:|---:|
| SPY weight | 50.0% | 41.2% | 100.0% |
| TLT weight | 50.0% | 58.8% | 0.0% |
| Total return | 45.82% | 30.25% | 157.28% |
| Annualized return | 5.71% | 3.97% | 14.93% |
| Annualized volatility | 12.26% | 12.03% | 19.97% |
| Sharpe ratio | 0.5145 | 0.3839 | 0.7971 |
| Maximum drawdown | −28.50% | −29.68% | −33.72% |

The maximum-Sharpe optimizer selected a 100% SPY allocation based on the full sample's estimated returns and covariance. It produced the highest historical Sharpe ratio in this comparison, alongside the highest volatility and deepest drawdown.

## Limitations

Expected returns were estimated from the same observations used to evaluate portfolio performance. This creates look-ahead bias in a strategy-selection context and can substantially overstate the usefulness of the estimated allocation.

The experiment uses a zero risk-free rate and does not include transaction costs, taxes, or realistic historical rebalancing. Results should be interpreted as an in-sample implementation check, not as evidence of future performance.

## Output files

The comparison script saves:
- `data/runs/portfolio_allocations.csv`
- `data/runs/portfolio_comparison.csv`

## Next steps

Build a historical backtesting framework that estimates expected returns and covariance using only past observations, rebalances at defined intervals, and accounts for transaction costs and portfolio turnover. Compare strategies using out-of-sample performance.