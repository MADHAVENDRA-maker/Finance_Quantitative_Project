# Quantitative Finance Research Platform

## Development Progress Update --- Robustness and Walk-Forward Validation

**Documentation date:** 28 October 2026\
**Project root:** `C:\DESKTOP-1\GITHUB_REPOS\Finance_Project_Updated`\
**Environment:** Windows PowerShell, Python 3.11.5 in `.venv`\
**Previous documentation:**
`backtesting_portfolio_analysis_progress_update_2026-10-28.md`

This update records work completed after the previous progress note. The
project name remains undecided; the distribution is `research-platform`
and the import package is `project_structure`. No Git repository has
been initialized. The user reports that Ruff, the targeted stateful
walk-forward tests, and the full test suite passed after the latest
changes.

------------------------------------------------------------------------

## 1. Executive Summary

The research platform now includes a ten-ETF historical data pipeline,
baseline out-of-sample portfolio backtests, dynamic charts, full-sample
allocation comparison, a 27-configuration robustness grid,
fixed-versus-adaptive comparisons, expanding walk-forward interval
selection, and a stateful walk-forward simulation. The stateful
simulation carries portfolio holdings across dates, accounts for drift
and transaction costs, and exposes audit fields for target, applied, and
post-return weights.

The machine-learning forecasting phase has **not** started. It is
intentionally on hold while the user discusses additional project ideas.

## 2. Environment and Data

-   Project directory:
    `C:\\DESKTOP-1\\GITHUB_REPOS\\Finance_Project_Updated`
-   Python: 3.11.5 in `.venv`; continue using Python 3.11 because of
    prior package/build issues.
-   Config: `configs/assets.yaml`
-   Assets: SPY, QQQ, IWM, EFA, EEM, TLT, IEF, GLD, VNQ, DBC.
-   Processed prices for each ETF: 4,230 rows, 2010-01-04 to 2026-10-27.
-   Aligned daily returns: 4,229 observations, 2010-01-05 to 2026-10-27.

The data pipeline was explicitly run with `start='2010-01-01'`. Its
default start date was `2020-01-01`, which could shorten existing
histories if run without an explicit date. Data refreshes can overwrite
raw/processed CSVs; back up any snapshot that must be retained.
Data-provider histories can be revised, and the last date is the latest
returned during the run, not a guarantee that every asset has a
finalized bar that day.

`load_asset_returns()` reads tickers from configuration, validates files
and date indices, aligns returns, and is reused across analysis scripts.

## 3. Baseline Out-of-Sample Backtest

**Settings:** 252-trading-day estimation lookback; 21-trading-day
rebalance interval; 10-basis-point transaction cost. Out-of-sample
period: 2011-01-04 to 2026-10-27; 3,977 observations.

Strategies: - **Equal Weight:** equal allocation across configured
assets at rebalance. - **Minimum Variance:** covariance-based
low-variance allocation. - **Maximum Sharpe:** return/covariance-based
allocation targeting high estimated Sharpe.

  Metric                                Equal Weight   Minimum Variance   Maximum Sharpe
  ----------------------------------- -------------- ------------------ ----------------
  Total return                               237.19%             72.13%          213.61%
  CAGR                                         8.01%              3.50%            7.51%
  Annualized volatility                       11.34%              5.26%           11.16%
  Sharpe ratio                                0.7359             0.6805           0.7048
  Maximum drawdown                           -23.18%            -18.26%          -28.07%
  Observations                                 3,977              3,977            3,977
  Total L1 turnover                           6.1002            12.7998          88.8475
  Sum of transaction-cost fractions          0.6100%            1.2800%          8.8848%

Equal Weight led on CAGR and Sharpe in this baseline, with much lower
turnover than Maximum Sharpe. Minimum Variance had the lowest volatility
and shallowest drawdown, but lower return. Maximum Sharpe's high
turnover and costs motivate robustness testing. These are historical
results under the current metric/cost conventions, not forecasts.

Outputs: - `data/runs/backtest_equal_weight.csv` -
`data/runs/backtest_minimum_variance.csv` -
`data/runs/backtest_maximum_sharpe.csv` -
`data/runs/backtest_comparison.csv`

## 4. Visualizations

`python plot_backtest_results.py` regenerated: -
`data/runs/backtest_cumulative_returns.png` -
`data/runs/backtest_drawdowns.png` -
`data/runs/backtest_rolling_sharpe.png` -
`data/runs/backtest_rolling_volatility.png` -
`data/runs/backtest_allocation_weights.png` -
`data/runs/backtest_strategy_turnover.png`

The allocation chart was generalized from two assets to dynamically
discover `weight_*` columns and validate finite values, long-only bounds
within tolerance, consistent columns, and weights summing to one.
Generation succeeded; visual inspection of every chart has not been
confirmed.

## 5. Full-Sample Allocation Comparison

`compare_allocations.py` now uses the shared loader. It evaluated 4,229
observations from 2010-01-05 through 2026-10-27.

  Asset     Equal Weight   Minimum Variance   Maximum Sharpe
  ------- -------------- ------------------ ----------------
  SPY             10.00%             13.04%            7.44%
  QQQ             10.00%              0.00%           27.13%
  IWM             10.00%              0.00%            0.00%
  EFA             10.00%              0.01%            0.00%
  EEM             10.00%              0.00%            0.00%
  TLT             10.00%              0.00%            0.00%
  IEF             10.00%             76.95%           53.86%
  GLD             10.00%              0.00%           11.57%
  VNQ             10.00%              0.00%            0.00%
  DBC             10.00%             10.01%            0.00%

  Metric                    Equal Weight   Minimum Variance   Maximum Sharpe
  ----------------------- -------------- ------------------ ----------------
  Total return                    3.0965             1.0356           3.1477
  Annualized return                8.77%              4.33%            8.85%
  Annualized volatility           11.64%              5.23%            7.66%
  Sharpe ratio                    0.7804             0.8356           1.1457
  Maximum drawdown               -23.08%            -15.38%          -21.52%

**Critical caveat:** these weights were estimated on the full sample and
evaluated on that same sample. This is an in-sample descriptive
comparison, not proof of out-of-sample superiority. Heavy IEF
concentration is also a useful warning about optimization concentration
and estimation risk.

## 6. Parameter Robustness Analysis

`robustness_analysis.py` tested 27 configurations: 3 strategies ×
rebalance intervals (5, 21, 63 days) × costs (0, 10, 25 bps). All
configurations used the same out-of-sample period.

Top ten by net Sharpe:

  --------------------------------------------------------------------------------------------
      Rank Strategy     Rebalance Cost bps     CAGR   Volatility      Net    Max DD   Total L1
                             days                                  Sharpe             turnover
  -------- ---------- ----------- -------- -------- ------------ -------- --------- ----------
         1 Maximum             63        0    8.46%       10.87%   0.8019   -24.29%    48.4266
           Sharpe                                                                   

         2 Maximum              5        0    8.20%       10.86%   0.7803   -25.93%   179.8456
           Sharpe                                                                   

         3 Maximum             63       10    8.13%       10.87%   0.7736   -24.51%    48.4266
           Sharpe                                                                   

         4 Maximum             21        0    8.12%       11.16%   0.7554   -26.14%    88.8475
           Sharpe                                                                   

         5 Equal               63        0    8.15%       11.22%   0.7547   -22.49%     4.0479
           Weight                                                                   

         6 Equal               63       10    8.12%       11.22%   0.7524   -22.49%     4.0479
           Weight                                                                   

         7 Equal               63       25    8.08%       11.22%   0.7489   -22.49%     4.0479
           Weight                                                                   

         8 Equal                5        0    8.11%       11.43%   0.7398   -23.51%    11.4678
           Weight                                                                   

         9 Equal               21        0    8.05%       11.34%   0.7393   -23.17%     6.1002
           Weight                                                                   

        10 Equal               21       10    8.01%       11.34%   0.7359   -23.18%     6.1002
           Weight                                                                   
  --------------------------------------------------------------------------------------------

Files in `data/runs/robustness/`: individual configuration outputs,
`robustness_comparison.csv`, `robustness_ranked_by_sharpe.csv`, and
`transaction_cost_sensitivity.csv`.

Less frequent rebalancing often reduced turnover and improved net
metrics, particularly for Maximum Sharpe. Equal Weight remained a
low-turnover baseline. The highest-ranked configuration is not
automatically the best choice: selecting from a grid creates selection
bias, and the 63-day interval cannot be called universally optimal.
Zero-cost runs are reference cases, not realistic cost assumptions.

## 7. Fixed Versus Adaptive Walk-Forward Baselines

`compare_walk_forward_baselines.py` compared fixed and adaptive
schedules over 2023-01-03 to 2026-10-23, 956 observations, with 10-bps
costs.

  ---------------------------------------------------------------------------------------------
  Strategy   Schedule      Total     CAGR   Volatility   Sharpe    Max DD   Total L1       Cost
                          return                                            turnover   fraction
  ---------- ---------- -------- -------- ------------ -------- --------- ---------- ----------
  Equal      Fixed 63d    67.39%   14.54%       10.67%   1.3259   -10.89%     0.7194     0.0007
  Weight                                                                             

  Equal      Fixed 5d     67.49%   14.56%       10.74%   1.3199   -11.15%     2.4475     0.0024
  Weight                                                                             

  Equal      Fixed 21d    67.07%   14.49%       10.70%   1.3184   -11.06%     1.1658     0.0012
  Weight                                                                             

  Equal      Adaptive     43.49%    9.99%       10.83%   0.9327   -13.44%     1.2778     0.0013
  Weight                                                                             

  Maximum    Fixed 21d    91.89%   18.74%       11.47%   1.5553   -10.27%    21.6249     0.0216
  Sharpe                                                                             

  Maximum    Fixed 63d    83.61%   17.37%       12.23%   1.3711   -11.16%    11.2737     0.0113
  Sharpe                                                                             

  Maximum    Fixed 5d     70.20%   15.05%       11.19%   1.3089   -11.69%    49.2986     0.0493
  Sharpe                                                                             

  Maximum    Adaptive     69.86%   14.99%       13.14%   1.1290   -21.07%    11.4605     0.0115
  Sharpe                                                                             

  Minimum    Fixed 63d    24.01%    5.84%        5.99%   0.9772    -7.25%     2.2144     0.0022
  Variance                                                                           

  Minimum    Fixed 21d    22.76%    5.55%        5.94%   0.9398    -6.96%     2.6796     0.0027
  Variance                                                                           

  Minimum    Fixed 5d     22.43%    5.48%        5.91%   0.9327    -6.96%     4.4024     0.0044
  Variance                                                                           

  Minimum    Adaptive     39.55%    9.18%       10.81%   0.8668   -13.38%     2.1441     0.0021
  Variance                                                                           
  ---------------------------------------------------------------------------------------------

Outputs: `data/runs/walk_forward_comparison/`.

Adaptive did not consistently outperform fixed schedules. Equal Weight
adaptive underperformed fixed schedules. Minimum Variance adaptive
returned more but had much higher volatility and drawdown. Maximum
Sharpe fixed 21-day rebalance had the strongest Sharpe in this
particular evaluation, not a universal result. Before drawing firm
conclusions, review the implementation for look-ahead leakage, timing of
decisions, and equivalent initialization/evaluation conventions.

## 8. Expanding Walk-Forward Validation

`walk_forward_validation.py` used: - 4,229 input observations,
2010-01-05 to 2026-10-27. - 10 assets; 252-day lookback; 10-bps costs. -
Candidate intervals 5, 21, 63 trading days. - Two calendar years of
initial selection history. - Reported evaluation period 2013-01-02 to
2026-10-27, 3,476 observations.

  ------------------------------------------------------------------------------
  Strategy        Total       CAGR   Volatility     Sharpe     Max DD    Average
                 return                                                    daily
                                                                        turnover
  ---------- ---------- ---------- ------------ ---------- ---------- ----------
  Equal         191.99%      8.08%       10.99%     0.7621    -22.49%     0.0008
  Weight                                                              

  Maximum       183.54%      7.85%       11.43%     0.7185    -24.51%     0.0192
  Sharpe                                                              

  Minimum        43.54%      2.65%        5.42%     0.5105    -19.17%     0.0031
  Variance                                                            
  ------------------------------------------------------------------------------

Outputs in `data/runs/walk_forward/`: - `walk_forward_decisions.csv` -
`walk_forward_returns.csv` - `walk_forward_summary.csv` -
`walk_forward_cumulative_returns.png`

Selection history grew from 501 observations in 2013 to 3,771 in 2026.
Equal Weight selected 63 days in most/all years; Minimum Variance mostly
selected 63 days with some 21-day and 5-day years; Maximum Sharpe
selected 21 days in 2013--2015, 5 days in 2016, and mostly 63 days
afterward. Keep the decision rule and the distinction between candidate
backtests and final realized holdings explicit when interpreting this
analysis.

## 9. Stateful Walk-Forward Validation

`stateful_walk_forward_validation.py` was successfully run. It simulates
a continuous portfolio rather than treating each candidate schedule as
an independent realized portfolio.

### Methodology

-   252-trading-day estimation lookback; candidate rebalance intervals
    of 5, 21, and 63 days.
-   10-basis-point transaction costs; two calendar years of initial
    interval-selection history.
-   Selects the interval using historical Sharpe calculated only from
    returns strictly before the test year; ties prefer longer intervals.
-   Carries holdings forward and allows them to drift with market
    returns.
-   At year boundaries, applies the selected interval; an interval
    change forces an immediate rebalance.
-   Calculates turnover relative to drifted holdings, applies costs, and
    calculates net portfolio returns.
-   Validates date order/uniqueness, missing and non-finite returns,
    invalid returns below -100%, intervals, rebalance target presence,
    and weight sums.

### Auditability fields

The implementation adds: - `target_weight_<asset>`: target weights on
rebalance dates; missing on non-rebalance dates. -
`applied_weight_<asset>`: weights used to calculate that day's return. -
`weight_<asset>`: post-return drifted holdings, retaining the prior
naming convention. - `interval_changed`: records when the selected
interval changes.

These fields distinguish the target portfolio, weights actually used for
a day's return, and the portfolio after market movement.

### Results

Evaluation period: 2013-01-02 to 2026-10-27; 3,476 observations.

  -----------------------------------------------------------------------------------------------------------
  Strategy       Total    CAGR   Volatility   Sharpe    Max DD  Avg daily   Rebalances   Total L1    Sum cost
                return                                           turnover                turnover   fractions
  ---------- --------- ------- ------------ -------- --------- ---------- ------------ ---------- -----------
  Equal        196.85%   8.21%       11.02%   0.7710   -22.53%     0.0008           56     2.7622      0.0028
  Weight                                                                                          

  Maximum      153.97%   6.99%       11.61%   0.6403   -23.50%     0.0183          127    63.7478      0.0637
  Sharpe                                                                                          

  Minimum       46.03%   2.78%        5.42%   0.5333   -18.96%     0.0030          212    10.5804      0.0106
  Variance                                                                                        
  -----------------------------------------------------------------------------------------------------------

Outputs in `data/runs/walk_forward_stateful/`: -
`walk_forward_decisions.csv` - `walk_forward_returns.csv` -
`walk_forward_summary.csv` - `walk_forward_cumulative_returns.png`

Metrics were unchanged after the auditability fields and validations
were added. Equal Weight led on return and Sharpe with much less
turnover than Maximum Sharpe. Minimum Variance retained the lowest
volatility and relatively shallow drawdown. Results depend on this
universe, historical period, estimation rules, and simplified cost
model.

## 10. Tests and Code Quality

The user confirmed that the following all passed after the latest
changes:

``` powershell
python -m ruff check stateful_walk_forward_validation.py tests/test_stateful_walk_forward.py
python -m pytest tests/test_stateful_walk_forward.py -v
python -m pytest -q
```

`tests/test_stateful_walk_forward.py` contains six tests: 1.
`test_select_interval_uses_only_prior_years` 2.
`test_select_interval_rejects_missing_historical_candidates` 3.
`test_make_yearly_decisions_uses_prior_years_only` 4.
`test_stateful_simulation_has_valid_returns_and_weights` 5.
`test_stateful_simulation_applies_new_interval_at_year_change` 6.
`test_transaction_cost_and_net_return_accounting`

One test initially failed because its fixture omitted one configured
candidate interval. The fixture was corrected to include all intervals,
after which the test passed. The user then confirmed Ruff, targeted
tests, and the full suite passed.

## 11. Limitations and Research Cautions

1.  Historical estimates are uncertain, especially mean returns used by
    Maximum Sharpe.
2.  Optimized allocations can concentrate heavily in IEF; add
    concentration and weight-stability diagnostics.
3.  The proportional transaction-cost model does not fully capture
    bid--ask spreads, market impact, taxes, liquidity, or execution
    slippage.
4.  Choosing a winner after ranking many configurations introduces
    selection bias.
5.  Adaptive methods must use only information available at each
    decision time.
6.  Full-sample in-sample results, fixed-schedule OOS results, expanding
    walk-forward results, and stateful results answer different
    questions and should not be conflated.
7.  Data providers can revise history; keep alignment and missing-data
    checks.
8.  The project is a research/backtesting platform, not a live trading
    system.
9.  Historical performance is not a guarantee of future performance.
10. Chart generation succeeded, but visual inspection of every chart has
    not been confirmed.

## 12. Status at This Checkpoint

**Completed:** Python 3.11 environment/package foundation; ten-ETF
configuration and data refresh; shared return loader; baseline OOS
backtest; six charts; allocation comparison; 27-case robustness grid;
fixed/adaptive comparison; expanding walk-forward validation; stateful
walk-forward simulation; auditability fields; six focused tests; Ruff
and full pytest reported passing.

**Not completed:** ML forecasting phase; final project name; confirmed
visual inspection of all charts; live trading or production deployment.
No conclusion that adaptive rebalancing consistently wins or that
in-sample metrics prove future superiority should be made.

## 13. Reproduction Commands

Run from the project root with `.venv` activated:

``` powershell
python backtest_allocations.py
python compare_allocations.py
python robustness_analysis.py
python compare_walk_forward_baselines.py
python walk_forward_validation.py
python stateful_walk_forward_validation.py
python plot_backtest_results.py
python -m ruff check .
python -m pytest -q
```

Refresh data from 2010 onward only when intended, because CSVs may be
overwritten:

``` powershell
python -c "from project_structure.data.pipeline import run_data_pipeline; data = run_data_pipeline(start='2010-01-01'); [print(f'{ticker}: {df.index.min().date()} to {df.index.max().date()} | {len(df)} rows') for ticker, df in sorted(data.items())]"
```

## 14. Checkpoint Before ML

Before implementing ML, review the user's additional ideas and decide
which research question the model should answer. A possible future stage
is to compare rolling-volatility, EWMA, and GARCH baselines against a
regularized or tree-based model, evaluate out-of-sample MAE/RMSE/QLIKE,
and test whether forecasts improve portfolio decisions after costs. This
is a proposal only, not completed work. Existing volatility-forecasting
scripts/results should be inspected first to avoid duplicating earlier
work.

------------------------------------------------------------------------

**End of progress update --- 28 October 2026.**