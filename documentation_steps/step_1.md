# Market Data Ingestion, Cleaning, and Processing

## 1. Overview

This document records the development of the market-data infrastructure for the quantitative finance research platform built in:

`C:\DESKTOP-1\GITHUB_REPOS\Finance_Project_Updated`

The initial project setup established the Python environment, package structure, ETF configuration, and configuration validation. This development stage extended that foundation by implementing historical market-data downloading, data cleaning, and an end-to-end processing pipeline.

The main objective was to establish a reliable data foundation before developing portfolio analytics, risk measurement, forecasting, and backtesting.

### Components developed

1. Historical ETF data downloader.
2. Automated tests for data downloading.
3. Historical price-data cleaning and validation.
4. Automated tests for data cleaning.
5. End-to-end market-data processing pipeline.
6. Automated tests for pipeline behaviour.

The downloader, cleaning module, and pipeline were subsequently exercised and confirmed to work.

---

## 2. Historical Market-Data Downloader

### 2.1 File created

`src/project_structure/data/downloader.py`

The downloader uses `yfinance` to retrieve daily historical market data.

Its primary functions are:

- `download_asset_history()`
- `download_universe()`

### 2.2 Downloading one asset

The `download_asset_history()` function accepts a ticker, a start date, and an optional end date.

It requests daily historical observations through Yahoo Finance and returns the result as a pandas DataFrame.

The implementation includes the following safeguards:

- Removes surrounding whitespace from ticker symbols and converts them to uppercase.
- Rejects an empty ticker symbol.
- Checks that the start date precedes the end date.
- Requests daily observations with `auto_adjust=False`.
- Disables the separate actions columns in the returned history.
- Converts API exceptions into a descriptive `RuntimeError`.
- Raises an error when the provider returns no observations.
- Standardizes the date index name to `Date`.

**Why use `auto_adjust=False`?**

Keeping automatic adjustment disabled preserves the provider's separate price fields, including `Close` and, when supplied, `Adj Close`. This allows later calculations to explicitly select the appropriate price series instead of silently mixing adjusted and unadjusted prices.

### 2.3 Downloading the ETF universe

The `download_universe()` function supports downloading either:

- All ETFs defined in `configs/assets.yaml`; or
- A selected list of ticker symbols.

Its responsibilities include:

1. Loading the configured ETF universe when no ticker list is provided.
2. Normalizing ticker symbols.
3. Rejecting empty selections and duplicate tickers.
4. Validating the requested date range.
5. Downloading the selected assets.
6. Saving each asset's history as a CSV file.
7. Returning the downloaded DataFrames for subsequent processing.

Each asset is saved under its ticker symbol, for example:

- `data/raw/SPY.csv`
- `data/raw/TLT.csv`

The downloader collects the requested histories before writing the new batch of CSV files. This reduces the risk of creating a newly downloaded partial universe when an earlier download fails.

It does not guarantee an atomic filesystem transaction if a file-writing operation fails.

### 2.4 Dependency

The downloader uses the `yfinance` dependency already declared in `pyproject.toml`.

No separate environment or Python installation is required.

---

## 3. Downloader Testing

### 3.1 Test file

`tests/test_downloader.py`

Seven automated tests were added.

| Test | Purpose |
|---|---|
| Successful historical download | Checks the returned DataFrame and requested dates. |
| Empty download | Ensures empty provider responses raise an error. |
| API failure | Checks that download exceptions are wrapped with a descriptive error. |
| CSV output | Verifies that the selected ticker files are saved correctly. |
| Empty ticker selection | Rejects an empty list of tickers. |
| Duplicate tickers | Rejects repeated symbols, including case variations. |
| Invalid date range | Rejects a start date later than the end date. |

The tests mock the external Yahoo Finance interface where appropriate. This makes the automated tests reproducible without relying on live market-data access.

### 3.2 Real-data smoke test

A real download was performed for SPY and TLT over the January 2025 date range.

The test used:

- Start date: `2025-01-01`
- End date: `2025-02-01`

The user confirmed that the files downloaded successfully.

This verified that the downloader worked against the external data provider, rather than only against mocked responses.

---

## 4. Historical Price-Data Cleaning

### 4.1 File created

`src/project_structure/data/cleaning.py`

The cleaning module implements:

`clean_price_history()`

Its purpose is to convert historical price observations into a validated and chronologically ordered DataFrame suitable for subsequent calculations.

The module uses pandas for data manipulation and NumPy for numerical validation.

### 4.2 Required data fields

The following OHLCV fields are required:

- `Open`
- `High`
- `Low`
- `Close`
- `Volume`

Additional fields, such as `Adj Close`, are preserved when available.

### 4.3 Validation and cleaning rules

**Date handling**

- Accepts dates supplied in a `Date` column or as the DataFrame index.
- Converts dates to pandas datetime values.
- Rejects invalid dates and duplicate dates.
- Standardizes the index name to `Date`.
- Sorts the resulting observations chronologically.

**Required columns**

The function checks that all five OHLCV columns exist. Missing required columns result in a descriptive error.

**Missing values**

Rows with missing values in required OHLCV fields are removed.

If no usable observations remain, the function raises an error.

Missing prices are not forward-filled, and missing returns are not replaced with zero. This avoids introducing artificial observations into financial calculations.

**Numerical validation**

- Converts required fields to numeric values.
- Rejects infinite or otherwise non-finite values.
- Requires positive opening, high, low, and closing prices.
- Rejects negative volume.

**OHLC consistency**

The function checks that:

- The daily high is not below the daily low.
- The daily high is at least as large as the open and close.
- The daily low is no greater than the open and close.

These checks identify internally inconsistent price records.

### 4.4 Important limitation

The cleaning function validates internal consistency; it does not establish that every observation is economically correct.

It also does not manufacture missing trading days. Weekends and market holidays are expected to be absent from daily market data.

The current validation rules are intended for conventional ETF OHLCV data. Other instruments may require different validation rules.

---

## 5. Cleaning Tests

### 5.1 Test file

`tests/test_cleaning.py`

Eight automated tests were added.

| Test | Purpose |
|---|---|
| Chronological ordering | Verifies that dates are sorted. |
| Missing values | Checks that incomplete OHLCV observations are removed. |
| Duplicate dates | Ensures duplicate dates are rejected. |
| Nonpositive prices | Rejects zero or negative prices. |
| Inconsistent OHLC data | Detects invalid high and low relationships. |
| Missing required column | Rejects incomplete schemas. |
| Date-column support | Verifies that a `Date` column can be used instead of an index. |
| Empty data | Ensures an empty DataFrame raises an error. |

The tests use synthetic data, so they do not depend on the availability of Yahoo Finance.

The user confirmed that Ruff and the test suite worked after correcting import formatting.

---

## 6. End-to-End Market-Data Pipeline

### 6.1 File created

`src/project_structure/data/pipeline.py`

The pipeline implements:

`run_data_pipeline()`

This function connects downloading and cleaning into one repeatable workflow.

### 6.2 Pipeline sequence

The workflow is:

1. Select the configured ETF universe or a user-specified ticker list.
2. Download the historical data.
3. Retain the raw downloads in the raw-data directory.
4. Clean and validate every downloaded DataFrame.
5. Complete validation for the batch before writing processed CSV files.
6. Save the validated datasets in the processed-data directory.
7. Return the cleaned DataFrames for further analysis.

### 6.3 Output directories

The project now distinguishes raw and processed datasets.

| Directory | Purpose |
|---|---|
| `data/raw/` | Original downloaded market-data files. |
| `data/processed/` | Cleaned and validated market-data files. |

For example:

```text
data/
├── raw/
│   ├── SPY.csv
│   └── TLT.csv
├── processed/
│   ├── SPY.csv
│   └── TLT.csv
└── runs/
```

The `runs/` directory remains available for future experiment outputs.

Keeping raw data separate from processed data makes the workflow easier to inspect and debug. It also allows the cleaning logic to be changed without losing the original downloads.

### 6.4 Validation before saving

The pipeline cleans all downloaded DataFrames before writing the processed batch.

If a later DataFrame fails validation, the function raises an error before writing any of the new processed files in that batch.

This behaviour was tested with a deliberately invalid price.

It does not guarantee atomic replacement of previously existing files if an error occurs during the subsequent filesystem writes.

### 6.5 Pipeline tests

Test file:

`tests/test_pipeline.py`

Two automated tests were added:

1. **Successful processing:** verifies that cleaned CSV files are produced for SPY and TLT.
2. **Validation failure:** verifies that the pipeline does not create the processed output directory when a dataset fails validation before writing begins.

The downloader is mocked in these tests, keeping them independent of the external provider.

The user subsequently confirmed that the end-to-end pipeline worked.

---

## 7. Current Project Structure

The relevant project structure now includes:

```text
Finance_Project_Updated/
├── configs/
│   └── assets.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── runs/
├── documentation_steps/
│   ├── project_setup_and_configuration.md
│   └── market_data_ingestion_and_processing.md
├── src/
│   └── project_structure/
│       ├── __init__.py
│       ├── config.py
│       └── data/
│           ├── __init__.py
│           ├── downloader.py
│           ├── cleaning.py
│           └── pipeline.py
├── tests/
│   ├── test_config.py
│   ├── test_downloader.py
│   ├── test_cleaning.py
│   └── test_pipeline.py
├── .gitignore
└── pyproject.toml
```

This structure lists the expected project files. The documentation filenames shown here should be checked against the actual folder; the current document should be saved at the path specified at the beginning of this file.

The existing configuration module, ETF configuration, project metadata, Python environment, and Git-ignore rules remain in place. Git has not been initialized, in accordance with the project decision to postpone it.

---

## 8. Testing and Code Quality

The project uses:

- **pytest** for automated testing.
- **Ruff** for linting and import organization.

The import-order checks identified minor issues during development. These were corrected using Ruff's automatic fix option.

For example:

```powershell
python -m ruff check src/project_structure/data/cleaning.py --fix
```

The full-project lint command is:

```powershell
python -m ruff check src tests
```

The automated test suite is run using:

```powershell
python -m pytest -v
```

### Test-count progression

| Development stage | Tests added | Cumulative expected tests |
|---|---:|---:|
| Configuration | 6 | 6 |
| Downloader | 7 | 13 |
| Cleaning | 8 | 21 |
| Pipeline | 2 | 23 |

The cumulative count is **23 tests** after the pipeline stage. The individual stages were reported as working during development.

The commands above should be rerun whenever code changes are made; the expected test count is not a substitute for checking the actual test output.

---

## 9. Design Decisions and Rationale

### Separate downloading, cleaning, and orchestration

Each component has a distinct responsibility:

- `downloader.py` retrieves external data and saves raw CSVs.
- `cleaning.py` validates and cleans individual historical datasets.
- `pipeline.py` coordinates the two and manages processed outputs.

This separation makes each component easier to test and modify independently.

### Preserve raw observations

The original downloads remain separate from the processed files. This prevents the cleaning process from overwriting the source observations and makes debugging easier.

### Fail explicitly on invalid data

The implementation raises errors for invalid tickers, empty downloads, duplicate dates, missing required columns, invalid prices, and inconsistent OHLC values.

Failing explicitly is preferable to silently generating misleading data for later portfolio calculations.

### Use synthetic data in unit tests

Mocked provider responses and synthetic DataFrames keep most tests fast, repeatable, and independent of network conditions.

Real provider access is tested separately through a small smoke test.

### Avoid premature expansion

The current implementation focuses on obtaining and validating daily ETF data. Forecasting, optimization, trading strategies, and dashboard functionality remain separate future stages.

---

## 10. Current Status and Next Development Stage

The market-data infrastructure now supports:

- A configured ETF universe.
- Daily historical price downloading.
- Raw CSV storage.
- Price-data validation and cleaning.
- Processed CSV storage.
- An end-to-end processing function.
- Automated tests for the implemented components.

The next proposed module is:

`src/project_structure/data/returns.py`

Its intended responsibilities are:

1. Calculate simple daily returns.
2. Calculate logarithmic daily returns.
3. Prefer adjusted closing prices when available.
4. Align multiple assets by date.
5. Preserve missing observations instead of replacing them with zero.
6. Validate the input price series before calculating returns.

The proposed tests belong in:

`tests/test_returns.py`

**Status distinction:** the returns-calculation code and test cases have been drafted in the development conversation, but they have not yet been confirmed as executed successfully. They should be treated as the next implementation step rather than a verified component.

After the returns module is validated, the next logical development stage is descriptive financial statistics and risk metrics, followed by portfolio construction and backtesting.

---

## 11. Commands for Future Verification

Activate the project's existing Python 3.11 virtual environment before running project commands.

From the project root, use:

```powershell
python --version
python -m pip check
python -m ruff check src tests
python -m pytest -v
```

To rerun the small end-to-end pipeline test against Yahoo Finance:

```powershell
python -c "from project_structure.data.pipeline import run_data_pipeline; data=run_data_pipeline(tickers=['SPY','TLT'], start='2025-01-01', end='2025-02-01'); [print(t, '| rows:', len(df), '| first:', df.index.min(), '| last:', df.index.max()) for t, df in data.items()]"
```

This command uses a historical date range and depends on external data availability and network access.

## Conclusion

This development stage established the first complete data-processing workflow for the quantitative finance platform. Historical ETF observations can be downloaded, validated, cleaned, and stored in separate raw and processed directories. Automated tests provide coverage for common data-quality failures and the pipeline's core behaviour.

The next stage is to transform these validated price series into return series, which will form the foundation for quantitative analysis, portfolio risk measurement, and backtesting.