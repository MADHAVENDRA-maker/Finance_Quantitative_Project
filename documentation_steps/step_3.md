# Correlation and Covariance Analysis

## 1. Overview

This stage introduces correlation and covariance analysis into the quantitative research platform. These statistical measures help examine relationships between financial assets and provide a foundation for future portfolio construction, diversification analysis, and risk management.

The implementation is contained in:

- `src/project_structure/features/relationships.py`
- `tests/test_relationships.py`

The module currently supports correlation matrices, covariance matrices, and rolling correlations between two assets.

## 2. Implemented Functionality

### 2.1 Input Validation

The internal `_validate_returns()` function checks that the input is a valid pandas DataFrame containing numerical asset returns.

The validation process includes:

- Rejecting empty datasets.
- Rejecting duplicate asset columns.
- Rejecting missing observations.
- Rejecting non-numeric or non-finite values.
- Requiring at least two observations.
- Rejecting assets with zero return variance.

These checks help prevent invalid inputs from producing misleading statistical results.

### 2.2 Correlation Matrix

The `calculate_correlation_matrix()` function computes the Pearson correlation matrix of the supplied asset returns.

The Pearson correlation coefficient ranges from -1 to +1:

- A value close to +1 indicates a strong positive linear relationship.
- A value close to -1 indicates a strong negative linear relationship.
- A value close to zero indicates a weak linear relationship.

Correlation is dimensionless and can be used to compare relationships between assets with different return volatilities.

### 2.3 Covariance Matrix

The `calculate_covariance_matrix()` function calculates the sample covariance matrix using pandas' sample covariance convention, with a denominator of \(n-1\).

The diagonal entries represent the sample variance of individual asset returns, while the off-diagonal entries represent the covariance between pairs of assets.

Covariance is sensitive to the scale of the input data. When daily returns are supplied, the output represents daily return covariance and is not automatically annualized.

### 2.4 Rolling Correlation

The `calculate_rolling_correlation()` function calculates the Pearson correlation between two specified assets over a moving window.

The window parameter represents the number of observations rather than calendar days. For example, a window of 60 represents 60 return observations.

The first \(w-1\) observations are NaN for a window of size \(w\), since the calculation requires a complete window.

Rolling correlations can help investigate whether the relationship between assets changes across different periods and market conditions.

## 3. Testing and Validation

Automated tests are maintained in `tests/test_relationships.py`.

The 11 tests cover:

1. Correlation matrix dimensions and asset labels.
2. Symmetry of the correlation matrix.
3. Valid bounds for correlation coefficients.
4. Symmetry of the covariance matrix.
5. Agreement between covariance diagonal entries and individual sample variances.
6. Expected warm-up observations for rolling correlation.
7. Valid bounds for rolling correlation coefficients.
8. Rejection of missing observations.
9. Rejection of assets with zero variance.
10. Rejection of invalid rolling-window sizes.
11. Rejection of unknown asset names.

The project was validated using:

```powershell
python -m ruff check src tests
python -m pytest -v
```

The user confirmed that the tests passed. This validates the implemented test cases and confirms that the new module integrates with the existing project code.

## 4. Empirical Validation Using SPY and TLT

The module was tested using processed price histories for:

- **SPY:** an exchange-traded fund tracking the S&P 500.
- **TLT:** an exchange-traded fund holding long-duration US Treasury bonds.

Returns were calculated using the existing return-calculation module. Rows with missing returns were removed to establish a common evaluation period.

The resulting dataset contained 19 aligned daily return observations.

### 4.1 Correlation Results

| | SPY | TLT |
|---|---:|---:|
| SPY | 1.0000 | 0.3236 |
| TLT | 0.3236 | 1.0000 |

The observed correlation between SPY and TLT was approximately +0.3236. This indicates a moderately positive linear relationship within the selected sample.

Both assets therefore tended to move in the same direction more often than they moved in opposite directions during this period, although the relationship was not particularly strong.

This result describes only the selected historical observations and should not be interpreted as evidence of a stable long-term relationship.

### 4.2 Covariance Results

| | SPY | TLT |
|---|---:|---:|
| SPY | 0.000081 | 0.000021 |
| TLT | 0.000021 | 0.000050 |

The diagonal entries represent the sample variance of daily returns. SPY exhibited a higher estimated daily return variance than TLT during the sample.

The positive off-diagonal entries indicate positive sample covariance between the two assets.

The covariance matrix is symmetric, as expected. Its values are based on daily returns and have not been annualized.

### 4.3 Interpretation Limitations

The 19-observation sample was used primarily to validate the calculation pipeline. It is too short to support reliable conclusions about long-term correlation, volatility, or diversification benefits.

Financial asset relationships can change over time, particularly during periods of market stress. More extensive historical data and rolling analysis will be needed to evaluate whether the observed relationship persists.

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
└── features/
    ├── performance.py
    └── relationships.py

tests/
├── test_config.py
├── test_downloader.py
├── test_cleaning.py
├── test_pipeline.py
├── test_returns.py
├── test_performance.py
└── test_relationships.py
```

The project now supports market data downloading, cleaning, processing, return calculation, individual asset performance metrics, multi-asset performance comparisons, correlation matrices, covariance matrices, and rolling correlation calculations.

Portfolio optimization, backtesting, forecasting, and the interactive dashboard remain future development tasks.

## 6. Next Development Stage

The next stage will focus on extending the analysis into a more practical exploratory analysis workflow.

Planned tasks include:

- Running the analysis over a longer historical period.
- Examining rolling correlations between selected asset pairs.
- Visualizing correlation matrices using heatmaps.
- Plotting rolling correlations over time.
- Ensuring charts have meaningful labels, dates, and titles.
- Adding appropriate tests and validating the outputs.

A longer evaluation period will make the analysis more informative, although estimates will still be sensitive to market conditions and the selected time window.

## 7. Conclusion

The correlation and covariance analysis stage has been implemented and tested successfully. The platform can now examine relationships between asset returns through correlation matrices, covariance matrices, and rolling correlation calculations.

Validation using SPY and TLT demonstrated that the module works with the existing processed market data. The observed positive correlation of 0.3236 is specific to the short sample and should be treated as a functional validation rather than a reliable long-term estimate.

This stage establishes another important foundation for the platform's eventual portfolio construction and risk-analysis capabilities.