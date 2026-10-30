# Quantitative Research Platform
## Project Setup, Configuration and Validation — Development Log

**Last updated:** 26 October 2026  
**Status:** Initial environment setup and ETF configuration completed  
**Python version:** 3.11.5  
**Project distribution name:** `research-platform`  
**Python package:** `project_structure`

---

## 1. Project Overview

The objective is to build a modular quantitative research and portfolio analytics platform from the ground up. The platform will initially focus on exchange-traded funds (ETFs), with the architecture designed to support historical market-data ingestion, financial feature engineering, portfolio construction, backtesting, risk analysis, and forecasting.

The platform is being developed incrementally. Each component will be implemented and validated before proceeding to the next stage.

### Development principles

1. **Modularity:** Separate configuration, data ingestion, feature engineering, portfolio construction, backtesting, risk analysis, and forecasting into independent components.
2. **Reproducibility:** Keep raw market data separate from processed data and experiment outputs.
3. **Validation first:** Validate inputs and configurations before using them in calculations.
4. **Testability:** Add automated tests alongside the implementation of each component.
5. **Code quality:** Use Ruff for linting and pytest for automated testing.
6. **Controlled dependencies:** Install only the libraries needed for the current development stage.
7. **Incremental development:** Verify each stage before adding more complexity.
8. **Flexible asset selection:** Design the pipeline so that changing the selected ETF universe can eventually recompute the complete research workflow.

---

## 2. Project Location and Environment

**Project root:**

`C:\DESKTOP-1\GITHUB_REPOS\Finance_Project_Updated`

### Python environment

The project uses Python 3.11.5 in a dedicated virtual environment.

Virtual environment:

`.venv\Scripts\python.exe`

The environment was selected deliberately to keep the project isolated from other Python installations and to reduce the risk of dependency conflicts.

### Why use a virtual environment?

A dedicated virtual environment:

- Keeps project dependencies separate from global Python packages.
- Makes the environment easier to reproduce.
- Prevents unrelated projects from changing this project's dependencies.
- Makes package troubleshooting and upgrades more controlled.

### Verified environment

The following checks have been completed successfully:

| Check | Result |
|---|---|
| Python version | 3.11.5 |
| Python executable | Correct project `.venv` |
| Package installation | Successful |
| Dependency compatibility | No broken requirements |
| Ruff | 0.17.2; working correctly |
| pytest | 8.4.2; working correctly |
| Project import | `project_structure` imports successfully |

The environment is considered ready for continued development.

---

## 3. Project Metadata and Dependencies

The project metadata is defined in `pyproject.toml`.

### Build configuration

The project uses setuptools as its build backend.

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"
```

### Project metadata

```toml
[project]
name = "research-platform"
version = "0.1.0"
description = "A modular quantitative research and portfolio analytics platform"
requires-python = ">=3.11,<3.12"
```

The Python version restriction ensures that this project is developed and tested with Python 3.11 rather than unintentionally switching to another interpreter.

### Core dependencies

| Package | Purpose |
|---|---|
| NumPy | Numerical computing and array operations |
| pandas | Time-series data manipulation and analysis |
| SciPy | Scientific computing and numerical optimization |
| Pydantic | Input and configuration validation |
| PyYAML | Reading YAML configuration files |
| yfinance | Retrieving historical financial market data |

The dependency versions are constrained in `pyproject.toml` to reduce unexpected compatibility changes.

### Development dependencies

The `dev` optional dependency group contains:

- `pytest` — automated testing.
- `pytest-cov` — test coverage reporting.
- `ruff` — linting and code-quality checks.

Dashboard dependencies are defined separately under the optional `dashboard` group:

- Streamlit.
- Plotly.

They are kept optional because the initial priority is the research engine, not the user interface.

### Installation command

The editable installation was performed using:

```powershell
python -m pip install -e ".[dev]"
```

Editable installation means changes to the project source can be used without repeatedly reinstalling the project during ordinary development.

### Dependency verification

The following command returned:

```text
No broken requirements found.
```

Command:

```powershell
python -m pip check
```

This confirms that pip did not detect missing or incompatible declared dependencies in the installed environment.

---

## 4. Package Naming and Cleanup

Two names have distinct purposes:

- **Distribution name:** `research-platform`
- **Python package directory:** `src/project_structure/`

The distribution name is defined in `pyproject.toml`. The Python package directory determines how the application modules are imported.

The older distribution metadata named `quantlab` was left over from an earlier project setup.

It was removed using:

```powershell
python -m pip uninstall quantlab
```

The project was then reinstalled:

```powershell
python -m pip install -e ".[dev]"
```

Verification confirmed:

- `research-platform` is installed from the correct project directory.
- `quantlab` is no longer registered as an installed distribution.
- `project_structure` imports successfully from `src/project_structure/__init__.py`.

The Python package directory remains named `project_structure`.

---

## 5. Directory Structure and Repository Hygiene

The project has been organized around a `src`-based Python package layout.

The established structure includes:

```text
Finance_Project_Updated/
│
├── .venv/
├── .gitignore
├── pyproject.toml
│
├── configs/
│   └── assets.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── runs/
│
├── documentation_steps/
│
├── src/
│   └── project_structure/
│       ├── __init__.py
│       ├── config.py
│       ├── backtesting/
│       ├── data/
│       ├── features/
│       ├── forecasting/
│       ├── portfolio/
│       └── risk/
│
└── tests/
    └── test_config.py
```

Some listed directories are structural placeholders for future components; they do not imply that those components have already been implemented.

### Purpose of the main directories

**`configs/`**

Stores configuration files that control the application without requiring changes to Python source code.

**`data/raw/`**

Will hold original downloaded market data, preserving the source data before cleaning or transformation.

**`data/processed/`**

Will hold cleaned and standardized datasets used by downstream research components.

**`data/runs/`**

Will hold experiment outputs and run-specific artifacts.

**`src/project_structure/`**

Contains the actual Python application code, organized by responsibility.

**`tests/`**

Contains automated tests that verify application behavior.

**`documentation_steps/`**

Provides a location for development documentation and implementation notes.

### Why use a `src` layout?

The `src` layout separates application code from configuration files, tests, and other project artifacts. It also helps ensure that imports use the installed package rather than accidentally relying on the project root.

### `.gitignore`

A `.gitignore` file has been created to exclude items such as:

- Virtual environments.
- Python cache files.
- Environment variables and secrets.
- Test caches and coverage reports.
- Build artifacts.
- IDE-specific files.
- Logs and temporary files.
- Local raw data, processed data, and experiment outputs.

Placeholder files such as `.gitkeep` are allowed so that data directories can be retained in a future Git repository.

**Git has deliberately not been initialized.** The project will remain without a Git repository until that step is explicitly chosen.

---

## 6. ETF Universe Configuration

The first application-level configuration file is:

`configs/assets.yaml`

It defines ten ETFs that represent several different asset classes.

| Ticker | Asset class | Research purpose |
|---|---|---|
| SPY | US Equity | Large-cap US equities |
| QQQ | US Equity | Nasdaq-100 exposure |
| IWM | US Equity | US small-cap equities |
| EFA | International Equity | Developed markets outside the US and Canada |
| EEM | Emerging Markets Equity | Emerging-market equities |
| TLT | Long-Term US Treasury Bonds | Long-duration government bonds |
| IEF | Intermediate-Term US Treasury Bonds | Intermediate-duration government bonds |
| GLD | Gold | Gold exposure |
| VNQ | US Real Estate | US real estate investment trusts |
| DBC | Commodities | Broad commodity-futures exposure |

### Why these ETFs?

The initial universe provides exposure to different return drivers rather than focusing exclusively on US equities.

This creates a useful foundation for studying:

- Diversification across asset classes.
- Correlations between equity and bond returns.
- Portfolio volatility and drawdowns.
- Allocation strategies.
- Risk-adjusted performance.
- The effect of different asset universes on portfolio construction.

These ETFs are a starting research universe, not a recommendation to buy or hold them. Their suitability for any eventual investment strategy will need to be evaluated using appropriate data, assumptions, and out-of-sample testing.

### Configuration validation

The YAML file was loaded using PyYAML, and a validation command confirmed:

```text
ETF count: 10
Unique tickers: 10
Tickers: SPY, QQQ, IWM, EFA, EEM, TLT, IEF, GLD, VNQ, DBC
```

This establishes that the file contains ten entries with ten unique ticker symbols.

---

## 7. Configuration Loader

The configuration loader is implemented in:

`src/project_structure/config.py`

Its purpose is to provide a single, validated interface for reading the ETF universe.

### Pydantic models

Two models were implemented.

**`AssetConfig`**

Represents an individual configured asset and validates its required fields:

- `ticker`
- `name`
- `asset_class`
- `description`

**`AssetsConfig`**

Represents the complete asset universe and validates that the collection contains at least one asset and no duplicate ticker symbols.

### Important validation behavior

**Required fields:** Empty or missing required values are rejected.

**Ticker normalization:** Lowercase ticker symbols are converted to uppercase.

**Duplicate detection:** Duplicate ticker symbols are rejected.

**Unexpected fields:** Extra fields are forbidden to catch configuration mistakes early.

**Missing configuration file:** A `FileNotFoundError` is raised if the requested file does not exist.

**Relative paths:** Relative configuration paths are resolved against the project root.

**YAML structure:** The loader requires the top-level YAML content to be a mapping.

### Project-root resolution

The loader derives the project root from its own source-file location. This allows the default configuration to be found without relying on the terminal's current working directory.

The default configuration is:

`configs/assets.yaml`

### Public loading function

The main entry point is:

```python
load_assets_config()
```

It returns a validated `AssetsConfig` object.

An alternative path can also be provided when a different configuration file is required.

### Successful verification

The loader was tested from PowerShell using:

```powershell
python -c "from project_structure.config import load_assets_config; c=load_assets_config(); print('Assets loaded:', len(c.assets)); print('Tickers:', ', '.join(a.ticker for a in c.assets)); print('First asset:', c.assets[0].model_dump())"
```

The output confirmed that all ten assets loaded and the first asset contained the expected metadata.

---

## 8. Automated Testing

Automated tests are implemented in:

`tests/test_config.py`

The tests use pytest and validate both expected behavior and error handling.

### Tests implemented

| Test | What it verifies |
|---|---|
| `test_load_default_assets_config` | The default file loads ten assets with unique tickers |
| `test_ticker_is_normalized_to_uppercase` | Lowercase tickers are normalized |
| `test_duplicate_tickers_are_rejected` | Duplicate tickers raise a Pydantic validation error |
| `test_empty_required_field_is_rejected` | Empty required fields are rejected |
| `test_unexpected_asset_field_is_rejected` | Unrecognized fields are rejected |
| `test_missing_config_file_raises_error` | A missing file raises `FileNotFoundError` |

### Test execution

Command:

```powershell
python -m pytest -v
```

Final verified result:

```text
collected 6 items

tests/test_config.py::test_load_default_assets_config PASSED
tests/test_config.py::test_ticker_is_normalized_to_uppercase PASSED
tests/test_config.py::test_duplicate_tickers_are_rejected PASSED
tests/test_config.py::test_empty_required_field_is_rejected PASSED
tests/test_config.py::test_unexpected_asset_field_is_rejected PASSED
tests/test_config.py::test_missing_config_file_raises_error PASSED

6 passed
```

All six tests passed in approximately 0.19 seconds.

### Why automated tests matter

These tests provide a regression check for the configuration component. If a later code change breaks ticker normalization, duplicate detection, or file handling, the test suite can identify the problem before it propagates into the financial calculations.

---

## 9. Code Quality and Ruff

Ruff is the project's linting tool.

The initial linting check identified import-ordering issues in:

- `src/project_structure/config.py`
- `tests/test_config.py`

These issues were automatically corrected using:

```powershell
python -m ruff check src tests --fix
```

The code was then checked again:

```powershell
python -m ruff check src tests
```

Verified result:

```text
All checks passed!
```

The test suite was rerun after the fixes, and all six tests still passed.

### Why linting is part of the workflow

Linting helps maintain consistent imports and catches common code-quality problems early. Running it throughout development reduces the cost of fixing small issues as the codebase grows.

---

## 10. Current Implementation Status

### Completed

- [x] Created and verified the Python 3.11.5 virtual environment.
- [x] Installed the core dependencies.
- [x] Installed the development dependencies.
- [x] Configured project metadata in `pyproject.toml`.
- [x] Created the `.gitignore` file.
- [x] Established the `src/project_structure/` package structure.
- [x] Removed the obsolete `quantlab` distribution metadata.
- [x] Created and validated `configs/assets.yaml`.
- [x] Implemented the Pydantic configuration models.
- [x] Implemented the YAML configuration loader.
- [x] Added six automated configuration tests.
- [x] Fixed Ruff import-ordering issues.
- [x] Verified that all six tests pass.
- [x] Verified that Ruff reports no remaining issues.
- [x] Verified that `pip check` reports no broken requirements.
- [x] Confirmed that the current project imports correctly.

### Not yet implemented

- [ ] Market-data downloader.
- [ ] Market-data validation and cleaning.
- [ ] Raw-data persistence.
- [ ] Adjusted-price and return calculations.
- [ ] Feature engineering.
- [ ] Portfolio construction and optimization.
- [ ] Backtesting engine.
- [ ] Risk analytics.
- [ ] Forecasting models.
- [ ] Interactive dashboard.
- [ ] End-to-end integration tests.

The data directories and future module directories are structural foundations, not completed implementations.

---

## 11. Next Development Stage: Market-Data Ingestion

The next planned component is a historical market-data downloader using yfinance.

The planned module is:

`src/project_structure/data/downloader.py`

The data package should also contain:

`src/project_structure/data/__init__.py`

These files have not yet been confirmed as created.

### Planned workflow

1. Read the validated ETF universe using `load_assets_config()`.
2. Allow the caller to select all ETFs or a specified subset.
3. Download daily historical price data for the selected tickers.
4. Handle invalid tickers, network errors, and incomplete responses explicitly.
5. Validate date indexes, expected columns, missing observations, duplicate dates, and price validity.
6. Preserve the downloaded source data under `data/raw/`.
7. Keep cleaned datasets separate under `data/processed/`.
8. Add automated tests for data validation and failure cases.
9. Test a small ETF subset before downloading the full universe.

The exact download schema and persistence format will be finalized during implementation.

### Why this stage comes next

The configuration and environment layers are now stable. Market data is the next dependency because almost every later component—returns, portfolio optimization, backtesting, and risk measurement—depends on reliable historical prices.

Data validation should be implemented before more advanced analytics to prevent malformed observations from silently affecting financial results.

---

## 12. Recommended Validation Commands

Run these commands from the project root with `.venv` activated.

### Verify Python

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

### Verify dependency consistency

```powershell
python -m pip check
```

### Verify project installation

```powershell
python -m pip show research-platform
```

### Verify configuration loading

```powershell
python -c "from project_structure.config import load_assets_config; c=load_assets_config(); print(len(c.assets), [a.ticker for a in c.assets])"
```

### Run automated tests

```powershell
python -m pytest -v
```

### Run linting

```powershell
python -m ruff check src tests
```

These commands form the current baseline verification routine. Run the relevant checks after each meaningful change.

---

## 13. Important Development Decisions

The following decisions should be preserved as the project evolves:

1. Use Python 3.11 for this project.
2. Keep the Python package named `project_structure`.
3. Keep the distribution name `research-platform` unless there is a deliberate decision to change it.
4. Do not initialize Git until explicitly requested.
5. Keep core research functionality separate from dashboard functionality.
6. Keep raw and processed data separate.
7. Use the YAML configuration as the central source of truth for the ETF universe.
8. Validate data and configuration inputs before downstream calculations.
9. Add automated tests as each component is developed.
10. Build and validate the research engine before adding sophisticated forecasting or machine-learning methods.

---

## 14. Conclusion

The project has completed its initial environment and configuration phase. The Python environment is correctly configured, the core dependencies are installed, the ten-ETF universe is defined, and the configuration loader has been validated through six passing automated tests. Ruff also reports a clean result.

The foundation is ready for the next stage: implementing a tested historical market-data ingestion layer. The emphasis remains on correctness, reproducibility, modularity, and incremental validation before building more advanced quantitative research functionality.