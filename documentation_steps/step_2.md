# Performance Metrics and Risk Analysis

## 1. Overview

This stage extends the market data processing pipeline by introducing quantitative performance and risk metrics. The objective is to evaluate historical asset returns using consistent mathematical definitions and establish a foundation for later portfolio analysis.

The implementation is located in:

- `src/project_structure/features/performance.py`
- `tests/test_performance.py`

The module currently calculates performance metrics for individual assets and compares multiple assets using a common returns DataFrame.

## 2. Implemented Functionality

### 2.1 Individual Asset Performance Metrics

The function `calculate_performance_metrics()` accepts a pandas Series containing periodic simple returns and calculates five metrics.

**Total Return**

Measures the cumulative return over the evaluation period, accounting for compounding.

\[
R_{\text{total}}=\prod_{t=1}^{n}(1+r_t)-1
\]

where \(r_t\) is the simple return for period \(t\), and \(n\) is the number of observations.

**Annualized Return**

Estimates the compound annual growth rate implied by the observed returns.

\[
R_{\text{annualized}}=
\left[\prod_{t=1}^{n}(1+r_t)\right]^{m/n}-1
\]

where \(m\) represents the number of periods per year. For daily market data, the default is 252 trading periods.

**Annualized Volatility**

Measures the variability of periodic returns, scaled to an annual basis.

\[
\sigma_{\text{annualized}}=\sigma_r\sqrt{m}
\]

where \(\sigma_r\) is the sample standard deviation of periodic returns.

**Sharpe Ratio**

Measures excess return relative to return volatility.

\[
S=\frac{\overline{r-r_f}}{\sigma_r}\sqrt{m}
\]

Here, \(r_f\) is the periodic risk-free rate derived from the specified effective annual risk-free rate. The default annual risk-free rate is zero.

**Maximum Drawdown**

Measures the largest percentage decline from a previous peak in cumulative wealth during the evaluation period.

\[
D_t=\frac{W_t}{\max_{0\leq j\leq t}W_j}-1
\]

\[
D_{\max}=\min_t D_t
\]

The calculation includes the initial wealth level of 1.0, ensuring that a decline immediately after the beginning of the evaluation period is captured.

### 2.2 Multi-Asset Performance Comparison

The function `compare_assets()` accepts a DataFrame in which each column represents an asset and each row represents a return observation.

It calculates the five performance metrics for every asset and returns a DataFrame indexed by ticker. This allows assets to be compared in a consistent tabular format.

The function rejects missing observations rather than silently removing them. Before comparing assets, the evaluation period must therefore be aligned appropriately.

## 3. Validation and Error Handling

The module incorporates validation checks to reduce the risk of producing misleading metrics.

- Ensures individual returns are supplied as a pandas Series.
- Ensures multi-asset returns are supplied as a pandas DataFrame.
- Rejects empty input.
- Rejects missing or non-finite return observations.
- Rejects simple returns below -100%.
- Validates the annualization period and risk-free rate.
- Rejects duplicate asset columns.
- Rejects incomplete multi-asset return data rather than silently filling or dropping observations.
- Returns a NaN Sharpe ratio when the sample is too short or return volatility is zero, where the ratio cannot be meaningfully calculated.

These checks help ensure that invalid inputs do not silently generate apparently valid performance statistics.

## 4. Unit Testing

Unit tests are maintained in `tests/test_performance.py`.

The tests cover:

1. Compounding of total returns.
2. Calculation of annualized returns.
3. Annualized volatility.
4. Maximum drawdown, including the initial wealth level.
5. Handling of zero-volatility returns.
6. Rejection of missing returns.
7. Rejection of returns below -100%.
8. Multi-asset performance comparison.
9. Rejection of missing observations in a multi-asset comparison.

The project is validated using Ruff for linting and pytest for automated testing.

Commands used:

```powershell
python -m ruff check src tests
python -m pytest -v
```

The user reported that the earlier tests passed and that the real-data performance comparison executed successfully.

## 5. Empirical Validation Using SPY and TLT

The performance module was tested using downloaded and processed price histories for:

- **SPY:** SPDR S&P 500 ETF Trust, representing large-cap US equities.
- **TLT:** iShares 20+ Year Treasury Bond ETF, representing long-duration US Treasury bonds.

The processed CSV files were loaded, asset returns were calculated, and rows containing missing returns were removed to establish a common evaluation period.

The following command was used:

```powershell
python -c "import pandas as pd; from pathlib import Path; from project_structure.data.returns import calculate_universe_returns; from project_structure.features.performance import compare_assets; files={p.stem: pd.read_csv(p, index_col='Date', parse_dates=True) for p in Path('data/processed').glob('*.csv') if p.stem in ['SPY','TLT']}; returns=calculate_universe_returns(files); returns=returns.dropna(); print(compare_assets(returns).round(4))"
```

### Observed Results

| Metric | SPY | TLT |
|---|---:|---:|
| Total return | 0.0294 | 0.0022 |
| Annualized return | 0.4683 | 0.0292 |
| Annualized volatility | 0.1425 | 0.1126 |
| Sharpe ratio | 2.7651 | 0.3085 |
| Maximum drawdown | -0.0250 | -0.0260 |

The figures are expressed as decimals. For example, SPY's total return of 0.0294 corresponds to approximately 2.94%.

Within this sample, SPY produced a higher cumulative return and a higher Sharpe ratio than TLT. SPY also exhibited greater annualized volatility, while TLT experienced a slightly larger maximum drawdown.

### Interpretation Limitations

The evaluation used approximately 19 daily return observations from the downloaded January 2025 sample. This is sufficient to verify that the calculation pipeline executes, but not to establish reliable long-term performance estimates.

Annualized return and Sharpe ratio estimates can be particularly unstable over short samples. These figures should therefore be treated as a technical validation of the implementation, not as investment recommendations or evidence of future performance.

More meaningful analysis will require longer historical periods, consistent date alignment, and careful consideration of the evaluation window.

## 6. Current Project Architecture

The relevant components implemented so far are:

```text
src/project_structure/
├── config.py
├── data/
│   ├── downloader.py
│   ├── cleaning.py
│   ├── pipeline.py
│   └── returns.py
└── features/
    └── performance.py

tests/
├── test_config.py
├── test_downloader.py
├── test_cleaning.py
├── test_pipeline.py
├── test_returns.py
└── test_performance.py
```

The project currently supports market data acquisition, cleaning, processing, return calculation, and historical performance analysis. Portfolio construction, optimization, backtesting, forecasting, and the interactive dashboard remain future development stages.

## 7. Next Development Stage

The next stage will implement correlation and covariance analysis in the features module.

Planned functionality includes:

- Calculation of a correlation matrix across assets.
- Calculation of a covariance matrix from aligned returns.
- Rolling correlation analysis to investigate changes in asset relationships over time.
- Heatmap visualizations for correlation analysis.
- Unit tests for matrix dimensions, symmetry, valid input, and missing-data handling.

This functionality will help identify diversification relationships and provide inputs for future portfolio optimization.

For the next stage, a longer historical dataset should be used so that correlations and covariance estimates are not based on an unnecessarily small sample.

## 8. Conclusion

The performance-analysis stage establishes a working framework for evaluating historical asset returns using compounded total return, annualized return, annualized volatility, Sharpe ratio, and maximum drawdown. The module has been exercised on actual SPY and TLT data, and the user has reported successful execution alongside passing earlier tests.

This component builds upon the validated data pipeline and return calculations. It provides the performance-analysis foundation needed for the next stages of quantitative research, particularly correlation analysis, portfolio construction, and risk management.