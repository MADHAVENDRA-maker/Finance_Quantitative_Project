# Quantitative Finance Research Platform

## Development Progress Update --- Expanded ETF Universe and Historical Backtest

**Project directory:**
`C:\DESKTOP-1\GITHUB_REPOS\Finance_Project_Updated`\
**Documentation date:** 28 October 2026\
**Environment:** Windows PowerShell, Python 3.11 virtual environment
(`.venv`)\
**Previous documentation:**
`backtesting_portfolio_analysis_progress.md`\
**Scope:** Work completed after the previous documentation, through the
successful ten-ETF backtest and regeneration of all six backtest charts.

------------------------------------------------------------------------

## 1. Summary

The backtest has been expanded from two ETFs (SPY and TLT) to ten ETFs.
Processed price histories were refreshed to cover January 2010 onward.
The ten-asset backtest and strategy comparison completed successfully,
and all six visualizations were regenerated.

The latest `ruff` and `pytest` results have not yet been reported. They
remain the next validation step.

## 2. Project and Environment

-   Project root: `C:\DESKTOP-1\GITHUB_REPOS\Finance_Project_Updated`
-   Environment: `.venv`, Python 3.11.
-   Shell: Windows PowerShell.
-   Development approach: incremental implementation and validation.
-   No Git repository was initialized as part of this work.
-   The project name remains unfinalized.

## 3. Expanded Asset Universe

The configured asset universe is loaded from `configs/assets.yaml`. The
ten ETFs used by the latest backtest are:

  Ticker   Broad exposure
  -------- --------------------------------------------------------
  SPY      US large-cap equities
  QQQ      Nasdaq-100 / growth-oriented US equities
  IWM      US small-cap equities
  EFA      Developed markets equities excluding the US and Canada
  EEM      Emerging markets equities
  TLT      Long-duration US Treasury bonds
  IEF      Intermediate-duration US Treasury bonds
  GLD      Gold
  VNQ      US real estate investment trusts
  DBC      Broad commodities

These are concise exposure descriptions; an ETF's precise exposure
depends on its benchmark and holdings.

### Configuration-driven loading

`backtest_allocations.py` was updated so `load_asset_returns()` reads
tickers through `load_assets_config()` instead of hardcoding SPY and
TLT. The loader checks for missing or empty files, sorts dates when
necessary, rejects duplicate dates, aligns returns across assets, and
rejects an empty aligned return table.

## 4. Historical Data Refresh

### Problem identified

An initial ten-asset run showed that eight ETFs had histories beginning
in January 2010, while SPY and TLT began in January 2020. Inspection
showed that the downloader and pipeline defaults used `2020-01-01`;
running the pipeline without an explicit start date could overwrite the
older SPY/TLT raw histories with shorter histories.

### Resolution and verification

The pipeline was run with the explicit start date `2010-01-01`. A
subsequent check of `data/processed/*.csv` confirmed for **all ten
ETFs**:

-   First date: `2010-01-04`
-   Last date: `2026-10-27`
-   Rows per asset: `4,230`

The common date range was confirmed for DBC, EEM, EFA, GLD, IEF, IWM,
QQQ, SPY, TLT, and VNQ.

The aligned return table contains 4,229 observations, from `2010-01-05`
through `2026-10-27`. One fewer observation than price rows is expected
because calculating returns requires a previous price.

**Data-refresh caution:** The downloader can overwrite raw CSVs. A
backup was recommended before the refresh, but completion of that backup
was not confirmed in the available run log. Preserve a backup before
future data refreshes if the prior dataset must be retained. The end
date reflects the latest data returned by the provider during this run,
not a guarantee that every asset has a finalized bar for the current
calendar date.

## 5. Backtest Configuration

  Parameter                                       Setting
  ---------------------------- --------------------------
  Configured asset universe                       10 ETFs
  Requested historical start                   2010-01-01
  Available daily returns        2010-01-05 to 2026-10-27
  Lookback                               252 trading days
  Rebalancing interval                    21 trading days
  Transaction cost                        10 basis points
  Evaluation                                Out-of-sample
  Out-of-sample period           2011-01-04 to 2026-10-27
  Out-of-sample observations                        3,977

The lookback period is used for estimation before the out-of-sample
simulation begins.

### Strategies

1.  **Equal Weight:** equal allocation across the configured assets at
    each rebalance.
2.  **Minimum Variance:** uses historical covariance estimates and
    portfolio optimization to seek a low-variance allocation.
3.  **Maximum Sharpe:** uses historical return and covariance estimates
    to seek an allocation with a high estimated Sharpe ratio.

Strategy functions are in
`src/project_structure/backtesting/strategies.py`; the simulation engine
is in `src/project_structure/backtesting/engine.py`. The engine tracks
portfolio returns, drifted holdings, turnover, and proportional
transaction costs.

## 6. Latest Backtest Results

`python backtest_allocations.py` completed successfully.

  Metric                                Equal Weight   Minimum Variance   Maximum Sharpe
  ----------------------------------- -------------- ------------------ ----------------
  Total return                               237.19%             72.13%          213.61%
  Annualized return                            8.01%              3.50%            7.51%
  Annualized volatility                       11.34%              5.26%           11.16%
  Sharpe ratio                                0.7359             0.6805           0.7048
  Maximum drawdown                           -23.18%            -18.26%          -28.07%
  Observations                                 3,977              3,977            3,977
  Total L1 turnover                           6.1002            12.7998          88.8475
  Sum of transaction-cost fractions          0.6100%            1.2800%          8.8848%

These are historical results produced by the project's current metric
conventions, not forecasts or guarantees.

### Initial interpretation

-   **Equal Weight** had the highest total return, annualized return,
    and Sharpe ratio in this run. Turnover was substantially lower than
    Maximum Sharpe.
-   **Minimum Variance** had the lowest annualized volatility and
    shallowest maximum drawdown, but also the lowest return.
-   **Maximum Sharpe** did not outperform Equal Weight on annualized
    return or Sharpe ratio in this sample and had much higher turnover
    and transaction-cost fractions.

The Maximum Sharpe strategy may be sensitive to noisy historical mean
and covariance estimates. Its turnover makes robustness testing across
transaction costs and rebalance intervals particularly important.

### Saved outputs

Strategy files: - `data/runs/backtest_equal_weight.csv` -
`data/runs/backtest_minimum_variance.csv` -
`data/runs/backtest_maximum_sharpe.csv`

Comparison table: - `data/runs/backtest_comparison.csv`

The comparison table includes return, annualized return, volatility,
Sharpe ratio, maximum drawdown, observation count, dates, turnover, and
transaction-cost totals.

## 7. Visualization Regeneration

`python plot_backtest_results.py` completed successfully and regenerated
six charts under `data/runs/`:

1.  `backtest_cumulative_returns.png`
2.  `backtest_drawdowns.png`
3.  `backtest_rolling_sharpe.png`
4.  `backtest_rolling_volatility.png`
5.  `backtest_allocation_weights.png`
6.  `backtest_strategy_turnover.png`

The allocation-weight plotting function was generalized from the
previous two-asset SPY/TLT layout to discover `weight_*` columns in the
strategy results. It validates consistent weight columns across
strategies, finite weights, long-only bounds within a numerical
tolerance, and weights summing to one.

Successful script execution confirms that the six images were generated;
it does not confirm that each chart has been visually inspected or that
all automated tests pass.

## 8. Validation Status

  -----------------------------------------------------------------------
  Check                               Status
  ----------------------------------- -----------------------------------
  Processed-data date-range           Passed: all ten CSVs have 4,230
  verification                        rows from 2010-01-04 to 2026-10-27

  Ten-asset backtest                  Passed: outputs saved

  Visualization script                Passed: all six charts reported
                                      generated

  `python -m ruff check .`            Not yet reported after latest
                                      changes

  `python -m pytest -q`               Not yet reported after latest
                                      changes

  Visual inspection of all charts     Not yet confirmed
  -----------------------------------------------------------------------

Run the code-quality and test checks before further development:

``` powershell
python -m ruff check .
python -m pytest -q
```

Any failures should be investigated. Some tests or analysis scripts may
still assume a two-asset SPY/TLT universe.

## 9. Limitations and Research Considerations

1.  **Estimation risk:** Optimized strategies depend on historical
    estimates; mean-return estimates in particular can be noisy.
2.  **Simplified transaction costs:** The current proportional model
    does not fully model market impact, bid--ask spreads, taxes,
    liquidity, or execution slippage.
3.  **No live execution:** This is a research/backtesting system, not a
    brokerage-connected trading system.
4.  **No future-performance guarantee:** Historical results are not
    predictive.
5.  **Parameter sensitivity remains:** The current comparison uses a
    252-day lookback, 21-day rebalance interval, and 10-basis-point cost
    assumption.
6.  **Possible residual two-asset assumptions:** Additional scripts and
    tests have been identified for review; they have not yet been
    confirmed fully generalized.
7.  **Data coverage and revisions:** Providers can revise histories, and
    assets can have different trading calendars. Alignment and
    missing-data handling should continue to be checked.

## 10. Next Steps

1.  Run `python -m ruff check .` and `python -m pytest -q`; resolve
    failures.
2.  Visually inspect the regenerated charts, especially the ten-asset
    allocation chart.
3.  Review remaining scripts and tests for SPY/TLT-specific assumptions:
    -   `compare_allocations.py`
    -   `robustness_analysis.py`
    -   `compare_walk_forward_baselines.py`
    -   `stateful_walk_forward_validation.py`
    -   `walk_forward_validation.py`
    -   `tests/test_backtesting_visualization.py`
4.  Adapt and validate those scripts one at a time for the ten-asset
    universe.
5.  Rerun robustness analysis across transaction-cost and rebalance
    settings.
6.  Rerun walk-forward validation after generalization and testing.
7.  Proceed to the forecasting/machine-learning stage only after the
    baseline and robustness pipeline is reliable.

## 11. Reproduction Commands

Run from the project root with `.venv` activated.

``` powershell
# Refresh data from 2010 onward (may overwrite raw/processed CSVs)
python -c "from project_structure.data.pipeline import run_data_pipeline; data = run_data_pipeline(start='2010-01-01'); [print(f'{ticker}: {df.index.min().date()} to {df.index.max().date()} | {len(df)} rows') for ticker, df in sorted(data.items())]"

# Run the baseline backtest
python backtest_allocations.py

# Regenerate charts from saved results
python plot_backtest_results.py

# Validate style and tests
python -m ruff check .
python -m pytest -q
```

**End of progress update --- 28 October 2026.**