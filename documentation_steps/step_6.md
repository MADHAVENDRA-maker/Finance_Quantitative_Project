# Portfolio Optimization

## Objective

This stage introduces long-only minimum-variance portfolio optimization and compares the optimized allocation against an equal-weight baseline. It builds on the existing market-data pipeline, return calculations, covariance analysis, and portfolio analytics modules.

## Methods implemented

### Equal-weight allocation

The `calculate_equal_weights()` function assigns the same weight to every asset. For a two-asset portfolio, each asset receives 50%.

### Minimum-variance optimization

The `calculate_minimum_variance_weights()` function uses SciPy's SLSQP optimizer to minimize portfolio variance using the estimated covariance matrix.

The optimization applies these constraints:

- Each asset weight must be between 0 and 1.
- The sum of all portfolio weights must equal 1.
- The covariance matrix must be numeric, finite, symmetric, and positive semidefinite.

The implementation validates the optimizer's result and raises an error if optimization fails or the returned weights violate the constraints.

## Modules and tests

- `src/project_structure/portfolio/optimization.py`
- `tests/test_portfolio_optimization.py`
- `compare_allocations.py`

Ten unit tests cover equal-weight allocation, optimization constraints, expected results for a known covariance matrix, asset-label preservation, and invalid covariance matrices.

## Historical evaluation

The implementation was evaluated using daily SPY and TLT returns from January 3, 2020, to October 23, 2026, with 1,711 aligned observations.

| Metric | Equal weight | Minimum variance |
|---|---:|---:|
| SPY weight | 50.0% | 41.2% |
| TLT weight | 50.0% | 58.8% |
| Total return | 45.82% | 30.25% |
| Annualized return | 5.71% | 3.97% |
| Annualized volatility | 12.26% | 12.03% |
| Sharpe ratio | 0.5145 | 0.3839 |
| Maximum drawdown | −28.50% | −29.68% |

The optimized portfolio had slightly lower estimated volatility, but its historical return and Sharpe ratio were also lower, and its maximum drawdown was worse. These findings demonstrate that minimum-variance optimization targets risk as measured by variance rather than directly maximizing returns or risk-adjusted performance.

## Output files

The comparison script saves:

- `data/runs/portfolio_allocations.csv`
- `data/runs/portfolio_comparison.csv`

## Limitations

This is an in-sample comparison. The same historical observations are used to estimate the covariance matrix and evaluate portfolio performance. The results therefore do not represent a realistic out-of-sample trading simulation.

The analysis also does not yet model transaction costs, taxes, or changing portfolio weights through a historical rebalancing process. The current optimizer is long-only and does not use expected-return forecasts.

## Next steps

1. Implement maximum-Sharpe portfolio optimization with explicit assumptions about expected returns and the risk-free rate.
2. Develop a backtesting framework that estimates parameters using only information available at each rebalance date.
3. Incorporate transaction costs, turnover, and realistic portfolio rebalancing.
4. Evaluate portfolio performance out of sample and compare it with appropriate baselines.