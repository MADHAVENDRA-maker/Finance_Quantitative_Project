# Exploratory Financial Visualizations

## 1. Overview

This stage extends the quantitative research platform with visual tools for exploring relationships between financial assets. The objective is to convert the output of the existing statistical analysis modules into charts that make correlation patterns and changes over time easier to interpret.

The implementation is contained in:

- `src/project_structure/features/visualization.py`
- `tests/test_visualization.py`

The module uses Matplotlib to generate and save charts without requiring a graphical display. Generated chart files are stored in `data/runs/`.

## 2. Historical Data Extension

The historical market data pipeline was executed again for SPY and TLT, using a start date of January 1, 2020.

The existing pipeline was reused to download, clean, validate, and save the market data. The processed files are maintained in `data/processed/`, while the raw files remain in `data/raw/`.

The extended history provides a more suitable basis for examining changing relationships between assets than the earlier January 2025 sample.

## 3. Implemented Visualizations

### 3.1 Correlation Heatmap

The function `plot_correlation_heatmap()` accepts a correlation matrix and an output path.

It generates a heatmap in which:

- Each cell represents the correlation between a pair of assets.
- The colour scale ranges from -1 to +1.
- Each cell displays its numerical correlation value.
- The axes identify the relevant assets.
- A colour bar provides a reference for interpreting correlation strength.

The function validates the matrix dimensions, labels, numerical values, value range, and symmetry before creating the chart.

The resulting visualization makes it easier to identify assets with similar return patterns or potentially useful diversification relationships.

### 3.2 Rolling Correlation Chart

The function `plot_rolling_correlation()` plots the rolling Pearson correlation between two assets over time.

The chart includes:

- The selected asset pair.
- The rolling correlation series.
- A horizontal reference line at zero.
- A vertical range spanning approximately -1 to +1.
- Date and correlation axes.
- A title specifying the rolling window.

The default window is 60 observations, approximately three trading months for daily market data.

The first 59 observations are unavailable for a 60-observation rolling calculation because each estimate requires a complete window. The chart can reveal whether the relationship between two assets remains stable or changes across market conditions.

## 4. File Output

The generated visualizations are saved in the following locations:

```text
data/runs/
├── correlation_heatmap.png
└── spy_tlt_rolling_correlation.png
```

The heatmap summarizes correlations across the selected assets, while the rolling-correlation chart focuses on the time-varying relationship between SPY and TLT.

The plotting functions create their output directories when necessary and return the paths of the saved image files.

## 5. Testing and Validation

Automated tests are maintained in `tests/test_visualization.py`.

The six tests cover:

1. Successful generation of a correlation heatmap.
2. Rejection of a non-square correlation matrix.
3. Rejection of correlation values outside the permitted range.
4. Successful generation of a rolling-correlation chart.
5. Rejection of an unknown asset.
6. Use of Matplotlib's non-interactive Agg backend.

The module was validated using:

```powershell
python -m ruff check src tests
python -m pytest -v
```

The user confirmed that the commands completed successfully and all tests passed.

The visualization functions were also executed against the processed SPY and TLT market data, and both chart files were generated.

## 6. Current Project Architecture

The relevant project components now include:

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
    ├── relationships.py
    └── visualization.py

tests/
├── test_config.py
├── test_downloader.py
├── test_cleaning.py
├── test_pipeline.py
├── test_returns.py
├── test_performance.py
├── test_relationships.py
└── test_visualization.py
```

The platform now supports market data ingestion, data cleaning, return calculation, performance analysis, correlation and covariance analysis, rolling correlations, and saved visualizations.

Portfolio optimization, backtesting, forecasting, and the interactive dashboard remain future development stages.

## 7. Interpretation Considerations

Although the dataset now spans a longer historical period, correlation estimates remain sensitive to the selected assets, dates, and market conditions.

A rolling correlation is particularly useful because a single full-period coefficient can conceal changes in the relationship between assets. However, rolling estimates are themselves noisy and depend on the chosen window length.

Correlation also does not establish causation, and a historically low or negative correlation does not guarantee future diversification benefits.

These charts should therefore be used as exploratory analytical tools rather than standalone investment signals.

## 8. Next Development Stage

The next stage will introduce portfolio-level analysis and prepare the platform for portfolio construction.

Before optimization, the project should establish reliable portfolio calculations, including:

- Portfolio returns from asset returns and portfolio weights.
- Validation of portfolio weights.
- Portfolio volatility using the covariance matrix.
- Annualization conventions for return and risk.
- Unit tests for portfolio calculations and weight constraints.

This will connect the existing asset-level analytics to portfolio-level risk and return calculations. Portfolio optimization can then be implemented on top of a tested foundation.

## 9. Conclusion

The exploratory visualization stage has been implemented and validated successfully. The platform can now generate correlation heatmaps and rolling-correlation charts from processed market data.

These visualizations build on the existing returns and relationship-analysis modules, making it easier to investigate asset relationships over time. They also prepare the project for its next major milestone: portfolio-level return and risk calculations.