# Portfolio Analytics

## 1. Overview

This stage introduces portfolio-level calculations into the quantitative research platform. The earlier modules analyzed individual assets, performance metrics, and relationships between returns. The portfolio analytics module combines these capabilities to evaluate the return and risk of a weighted collection of assets.

The implementation is located in:

- `src/project_structure/portfolio/analytics.py`
- `tests/test_portfolio_analytics.py`

The module currently supports portfolio-weight validation, portfolio return calculations, and annualized portfolio volatility.

## 2. Implemented Functionality

### 2.1 Portfolio Weight Validation

The function `validate_portfolio_weights()` accepts portfolio weights as a pandas Series or a mapping from asset names to weights.

It checks that:

- The weights are not empty.
- Asset names are valid and unique.
- All weights are finite numerical values.
- The weights sum to one within a small numerical tolerance.

The implementation permits negative weights, which can represent short positions. Long-only constraints and other investment restrictions have not yet been implemented.

### 2.2 Portfolio Returns

The function `calculate_portfolio_returns()` calculates periodic portfolio returns from an asset-returns DataFrame and a set of portfolio weights.

The calculation is:

\[
r_{p,t}=\sum_{i=1}^{N}w_i r_{i,t}
\]

where \(w_i\) represents the portfolio weight of asset \(i\), and \(r_{i,t}\) represents its simple return during period \(t\).

The function aligns weights with return columns by asset name, checks that the assets match, and rejects missing or non-finite observations.

The calculation assumes that the portfolio is rebalanced to the specified weights at the beginning of each return period. It does not include transaction costs, taxes, slippage, or execution constraints.

### 2.3 Portfolio Volatility

The function `calculate_portfolio_volatility()` calculates portfolio volatility using a covariance matrix and portfolio weights.

Portfolio variance is:

\[
\sigma_p^2=\mathbf{w}^{T}\Sigma\mathbf{w}
\]

For daily covariance, annualized volatility is:

\[
\sigma_{p,\mathrm{annual}}=
\sqrt{252\,\mathbf{w}^{T}\Sigma\mathbf{w}}
\]

The function validates the covariance matrix, checks that its asset labels match the portfolio weights, and rejects non-finite or asymmetric matrices.

The annualization factor defaults to 252 periods per year. The covariance matrix must represent the corresponding periodic return frequency.

## 3. Unit Testing

Automated tests are maintained in `tests/test_portfolio_analytics.py`.

The 12 tests cover:

1. Validation of valid portfolio weights.
2. Rejection of weights that do not sum to one.
3. Rejection of non-finite weights.
4. Rejection of empty weights.
5. Calculation of portfolio returns using weighted asset returns.
6. Alignment of return columns with weights by asset name.
7. Rejection of missing return observations.
8. Rejection of mismatched assets.
9. Agreement between calculated volatility and a manual covariance-based calculation.
10. Correct annualization of portfolio volatility.
11. Rejection of mismatched covariance assets.
12. Rejection of asymmetric covariance matrices.

The project was validated using Ruff and pytest. The user confirmed that the previous tests passed and that the real-data portfolio calculation executed successfully.

## 4. Empirical Validation Using SPY and TLT

The portfolio analytics module was evaluated using processed historical price data for SPY and TLT.

A hypothetical portfolio was defined with the following weights:

| Asset | Portfolio weight |
|---|---:|
| SPY | 60% |
| TLT | 40% |

The two asset-return series were aligned, and the common dataset contained 1,711 daily return observations.

### 4.1 Observed Results

| Metric | Result |
|---|---:|
| Portfolio cumulative return | 65.00% |
| Annualized portfolio volatility | 13.06% |
| Return observations | 1,711 |

The cumulative return was calculated by compounding the daily portfolio returns. Annualized volatility was calculated using the sample covariance matrix and the specified portfolio weights.

The results demonstrate that the portfolio analytics module can combine the existing return and covariance calculations to produce portfolio-level statistics.

### 4.2 Interpretation Limitations

The results are historical and depend on the selected date range and the portfolio rebalancing assumption.

The implementation uses constant portfolio weights for each return period. It does not model transaction costs, taxes, slippage, financing costs, or other real-world trading frictions. Consequently, the results should not be treated as a realistic backtest or as a forecast of future investment performance.

## 5. Current Project Architecture

The relevant implemented components are:

```text
src/project_structure/
├── config.py
├── data/
│   ├── downloader.py
│   ├── cleaning.py
│   ├── pipeline.py
│   └── returns.py
├── features/
│   ├── performance.py
│   ├── relationships.py
│   └── visualization.py
└── portfolio/
    └── analytics.py

tests/
├── test_config.py
├── test_downloader.py
├── test_cleaning.py
├── test_pipeline.py
├── test_returns.py
├── test_performance.py
├── test_relationships.py
├── test_visualization.py
└── test_portfolio_analytics.py
```

The platform now supports data ingestion and processing, return calculations, performance metrics, correlation and covariance analysis, financial visualizations, portfolio returns, and portfolio volatility.

Portfolio optimization, realistic backtesting, forecasting, and the interactive dashboard remain future development tasks.

## 6. Next Development Stage

The next stage will implement portfolio optimization on top of the existing portfolio analytics module.

The planned initial optimizer will explore long-only allocations that sum to one. It will use historical expected returns and the covariance matrix to construct portfolios under clearly specified assumptions.

The implementation will require:

- Explicit portfolio constraints.
- A documented expected-return estimation method.
- A documented covariance estimation method.
- Optimization objectives such as minimum variance and maximum Sharpe ratio.
- Tests for weight constraints and optimizer output.
- Comparison against simple baseline allocations.

Optimization results will need to be evaluated cautiously because estimated returns and covariance matrices are uncertain. Out-of-sample evaluation and realistic backtesting will be necessary before making claims about strategy performance.

## 7. Conclusion

The portfolio analytics stage has established the basic mathematical operations required to evaluate weighted portfolios. It validates asset weights, calculates periodic portfolio returns, and estimates annualized portfolio volatility using a covariance matrix.

Validation using a 60% SPY and 40% TLT portfolio demonstrated that the module works with the extended historical dataset. This foundation prepares the project for portfolio optimization, followed by more realistic backtesting and risk evaluation.