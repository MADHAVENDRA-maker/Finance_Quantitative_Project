# Quantitative Finance Research Platform

## Development Progress Documentation --- Backtesting and Portfolio Analysis

**Project directory:**
`C:\DESKTOP-1\GITHUB_REPOS\Finance_Project_Updated`\
**Documentation scope:** Work completed after the previous project
documentation, through the portfolio allocation and turnover
visualization stage.\
**Environment:** Windows PowerShell, Python 3.11 virtual environment
(`.venv`)\
**Status:** Core backtesting, performance visualizations, rolling
metrics, and allocation diagnostics have been implemented and
successfully executed.

------------------------------------------------------------------------

## 1. Project Objective and Development Approach

The project is being developed as a reusable quantitative finance
research platform. The current focus is on establishing a reliable
research and backtesting foundation before expanding into more advanced
forecasting, machine learning, or user-interface capabilities.

Development has been incremental: 1. Implement a focused module. 2. Add
tests and validate behavior. 3. Run the code against the saved market
data. 4. Preserve working components while adding the next capability.

The existing backtest engine and baseline outputs are retained as the
reference implementation. No Git repository was initialized as part of
this work.

## 2. Current Data and Backtest Setup

### Asset universe

-   **SPY:** US equity-market ETF proxy.
-   **TLT:** Long-duration US Treasury bond ETF proxy.

The saved processed price data is located under `data/processed/`,
including `SPY.csv` and `TLT.csv`. The backtest script uses the
processed data and aligns the asset return series before simulation.

### Baseline configuration

  Parameter                             Baseline setting
  ----------------------------------- ------------------
  Lookback period                       252 trading days
  Rebalancing interval                   21 trading days
  Transaction cost                       10 basis points
  Performance frequency                            Daily
  Evaluation                               Out-of-sample
  Rolling risk window                    63 trading days
  Risk-free rate for rolling Sharpe        0% annualized

The current available return data spans approximately **3 January 2020
to 23 October 2026**. With the 252-trading-day lookback, the baseline
out-of-sample period begins on **4 January 2021** and ends on **23
October 2026**, containing **1,459 observations**.

## 3. Portfolio Strategies

The backtest currently compares three strategies:

1.  **Equal Weight** --- allocates equally across the assets at each
    rebalance.
2.  **Minimum Variance** --- uses historical covariance estimates and
    portfolio optimization to seek a low-variance allocation.
3.  **Maximum Sharpe** --- uses historical return/covariance estimates
    and portfolio optimization to seek a high estimated Sharpe ratio.

The strategy functions are in:

`src/project_structure/backtesting/strategies.py`

The strategies use historical information available to the strategy at
each rebalance. The maximum-Sharpe strategy can be sensitive to
estimation error, so its historical results should not be interpreted as
evidence of future outperformance.

## 4. Backtest Engine

The main implementation is:

`src/project_structure/backtesting/engine.py`

The public backtest entry point is
`run_backtest(asset_returns, strategy, lookback=252, rebalance_every=21, transaction_cost_bps=10.0)`.

### Implemented behavior

-   Validates asset return input, target weights, and backtest
    parameters.
-   Uses an initial lookback period before beginning out-of-sample
    evaluation.
-   Rebalances at the configured interval.
-   Models **portfolio weight drift** between rebalances as asset
    prices/returns change.
-   Calculates turnover relative to the portfolio's actual drifted
    weights immediately before rebalancing.
-   Applies transaction costs to the portfolio return on rebalance
    dates.
-   Records gross and net returns, turnover, transaction-cost fractions,
    portfolio weights, and cumulative return series.

### Transaction-cost convention

Transaction costs are represented as a proportional deduction from
portfolio value at the beginning of the period in which a rebalance
occurs. The engine does not separately adjust the relative asset weights
for the cost deduction; this is a simplifying modeling assumption.

Turnover is based on the engine's L1 weight-change convention. Its exact
interpretation should be kept consistent when comparing results and when
adding other transaction-cost models.

## 5. Baseline Backtest Results

The baseline was run with a 252-day lookback, 21-day rebalance interval,
and 10 bps transaction costs.

  ---------------------------------------------------------------------------
  Metric                   Equal Weight   Minimum Variance     Maximum Sharpe
  ------------------ ------------------ ------------------ ------------------
  Out-of-sample                   1,459              1,459              1,459
  observations                                             

  Total net return               19.59%             10.24%             62.89%

  Annualized return               3.14%              1.70%              8.79%
  (CAGR)                                                   

  Annualized                     11.74%             11.73%             15.36%
  volatility                                               

  Sharpe ratio                   0.3219             0.2022             0.6257

  Maximum drawdown              -28.94%            -29.42%            -26.11%

  Total L1 turnover              2.4122             4.4883            10.4871
  (sum of daily                                            
  turnover values)                                         

  Sum of                        0.2412%            0.4488%            1.0487%
  transaction-cost                                         
  fractions                                                
  ---------------------------------------------------------------------------

### Interpretation

-   Maximum Sharpe produced the highest historical total and annualized
    returns in this baseline run, as well as the highest Sharpe ratio.
-   It also had the highest turnover and annualized volatility among the
    three strategies.
-   Minimum Variance did not produce the lowest observed volatility in
    this particular two-asset sample, illustrating that a strategy's
    objective does not guarantee the best realized outcome in every
    sample.
-   These results are historical, sample-dependent, and sensitive to
    model assumptions. They are not forecasts or guarantees.
-   The sum of transaction-cost fractions is a diagnostic aggregation;
    it should not be interpreted as the exact cumulative portfolio loss
    attributable to costs.

The results are saved under `data/runs/`, including: -
`backtest_equal_weight.csv` - `backtest_minimum_variance.csv` -
`backtest_maximum_sharpe.csv` - `backtest_comparison.csv`

## 6. Performance and Risk Metrics

The project includes overall and rolling metrics.

### Overall metrics

The existing performance analytics calculate measures such as: - Total
return - Annualized return - Annualized volatility - Sharpe ratio -
Maximum drawdown - Turnover and transaction-cost diagnostics

### Rolling metrics

New module:

`src/project_structure/backtesting/rolling_metrics.py`

Implemented functions: -
`calculate_rolling_sharpe(net_returns, window=63, risk_free_rate=0.0)` -
`calculate_rolling_volatility(net_returns, window=63)`

The calculations use net returns: - Rolling Sharpe annualizes the
rolling mean excess return divided by the rolling sample standard
deviation. - The annual risk-free rate is converted to an equivalent
daily rate before calculating excess returns. - Rolling volatility uses
the rolling sample standard deviation (`ddof=1`) multiplied by the
square root of 252. - The first 62 rows are undefined for a
63-observation window because a full window is required. - A
zero-volatility window produces an undefined Sharpe ratio rather than an
infinite value.

The default risk-free rate is zero, so this is a simplifying assumption
rather than a full excess-return calculation against an observed
risk-free series.

## 7. Visualization Module

The visualization functions are maintained in:

`src/project_structure/backtesting/visualization.py`

The root script that loads saved backtest results and generates charts
is:

`plot_backtest_results.py`

The following six charts have been generated successfully:

  ---------------------------------------------------------------------------------
  Output file                                   Purpose
  --------------------------------------------- -----------------------------------
  `data/runs/backtest_cumulative_returns.png`   Compares cumulative out-of-sample
                                                net returns.

  `data/runs/backtest_drawdowns.png`            Compares drawdowns from previous
                                                wealth peaks.

  `data/runs/backtest_rolling_sharpe.png`       Compares 63-day annualized rolling
                                                Sharpe ratios.

  `data/runs/backtest_rolling_volatility.png`   Compares 63-day annualized rolling
                                                volatility.

  `data/runs/backtest_allocation_weights.png`   Shows recorded daily SPY and TLT
                                                weights for each strategy.

  `data/runs/backtest_strategy_turnover.png`    Compares daily turnover for each
                                                strategy.
  ---------------------------------------------------------------------------------

### Chart implementation details

-   Charts use the saved per-strategy backtest CSV files.
-   Rolling charts use `net_return`, keeping transaction costs reflected
    in the performance analysis.
-   Allocation charts use the recorded daily weights. They show weight
    drift between rebalance dates, not only target weights at
    rebalancing.
-   Allocation validation checks for required weight columns, finite
    values, weights within the allowed 0--1 range (with a small
    numerical tolerance), and weights summing to one.
-   Turnover visualization checks that the turnover values are present,
    finite, and non-negative.
-   Chart images are saved in `data/runs/` and can be regenerated by
    running `python plot_backtest_results.py`.

### Successful execution

The latest execution of `python plot_backtest_results.py` reported
successful generation of all six outputs: - Cumulative returns -
Drawdowns - Rolling Sharpe ratio - Rolling volatility - Allocation
weights - Strategy turnover

## 8. Tests and Code Quality

Test files relevant to this work include: -
`tests/test_backtesting_engine.py` -
`tests/test_backtesting_strategies.py` -
`tests/test_backtesting_rolling_metrics.py` -
`tests/test_backtesting_visualization.py`

Coverage includes engine behavior, strategy behavior, rolling metric
calculations, chart file creation, input validation, and
portfolio-weight checks.

The focused tests and the full test suite have been reported by the
developer as passing at the checkpoints before the latest plotting
additions. The latest plotting script itself has also run successfully.
For a reproducible final check after all changes, run:

``` powershell
python -m pytest -v
python -m ruff check src tests
```

If any files were modified after the last full test run, re-run these
checks to confirm the final repository state.

## 9. How to Regenerate Backtest Charts

From the project root with `.venv` activated:

``` powershell
python plot_backtest_results.py
```

This script reads the three strategy CSV files from `data/runs/` and
writes the six charts to the same directory. It does not re-run the
backtest; to regenerate the underlying results using the baseline
configuration, run:

``` powershell
python backtest_allocations.py
```

Then run the plotting script again.

## 10. Important Limitations and Research Considerations

1.  **Limited asset universe:** Current results use only SPY and TLT.
    They do not represent a diversified multi-asset portfolio.
2.  **Historical estimation risk:** Optimized strategies depend on
    estimates derived from historical data. The maximum-Sharpe strategy
    in particular may be sensitive to noisy estimates.
3.  **Transaction-cost simplification:** The current cost model is
    proportional and does not model market impact, bid--ask spreads,
    taxes, or liquidity constraints.
4.  **No explicit financing or leverage model:** The current analysis
    should not be treated as a complete implementation model for a live
    portfolio.
5.  **Zero risk-free rate in rolling Sharpe:** The default rolling
    Sharpe metric assumes a zero annual risk-free rate unless configured
    otherwise.
6.  **Parameter sensitivity not yet completed:** The baseline ranking
    has not yet been stress-tested systematically across different
    transaction costs and rebalance intervals.
7.  **No live trading:** The project is a research/backtesting system,
    not a brokerage-connected or live-trading system.
8.  **Historical performance is not predictive:** Reported results
    should be used for evaluation and debugging, not as a promise of
    future returns.

## 11. Next Planned Stage --- Robustness Analysis

The next planned development stage is a controlled sensitivity analysis.
It has **not yet been implemented or run**.

Proposed experiment: - Transaction costs: 0, 10, and 25 basis points. -
Rebalancing intervals: 5, 21, and 63 trading days. - Strategies: Equal
Weight, Minimum Variance, Maximum Sharpe.

This would produce 27 strategy/configuration combinations. The
experiment should keep the asset universe, return data, and 252-day
lookback fixed, save results separately from the baseline files, and
compare annualized return, volatility, Sharpe ratio, maximum drawdown,
and turnover. The results should also identify whether strategy rankings
change under different assumptions.

Before implementation, the existing `backtest_allocations.py` and
strategy interfaces should be inspected to reuse their data-loading and
evaluation logic rather than duplicating it.

------------------------------------------------------------------------

**End of current progress documentation.**