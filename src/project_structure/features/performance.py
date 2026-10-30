import numpy as np
import pandas as pd


def calculate_performance_metrics(
    returns: pd.Series,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> dict[str, float]:
    """Calculate annualized performance and risk metrics from simple returns.

    Args:
        returns: A dated or undated Series of simple periodic returns.
        periods_per_year: Number of periods used for annualization.
        risk_free_rate: Effective annual risk-free rate, expressed as a decimal.

    Returns:
        A dictionary of total return, annualized return, annualized volatility,
        Sharpe ratio, and maximum drawdown.
    """

    if not isinstance(returns, pd.Series):
        raise TypeError("Returns must be supplied as a pandas Series.")

    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive.")

    if not np.isfinite(risk_free_rate) or risk_free_rate <= -1:
        raise ValueError("risk_free_rate must be finite and greater than -1.")

    if returns.empty:
        raise ValueError("Returns must not be empty.")

    if returns.isna().any():
        raise ValueError("Returns contain missing values.")

    values = pd.to_numeric(returns, errors="raise").to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise ValueError("Returns contain infinite or invalid values.")

    if (values < -1).any():
        raise ValueError("Simple returns cannot be less than -100%.")

    clean_returns = pd.Series(values, index=returns.index, dtype=float)

    wealth = (1.0 + clean_returns).cumprod()
    total_return = float(wealth.iloc[-1] - 1.0)

    if (wealth <= 0).any():
        raise ValueError("Portfolio wealth must remain positive.")

    annualized_return = float(
        wealth.iloc[-1] ** (periods_per_year / len(clean_returns)) - 1.0
    )

    annualized_volatility = float(
        clean_returns.std(ddof=1) * np.sqrt(periods_per_year)
    )

    daily_risk_free_rate = (1.0 + risk_free_rate) ** (
        1.0 / periods_per_year
    ) - 1.0

    excess_returns = clean_returns - daily_risk_free_rate
    daily_volatility = float(clean_returns.std(ddof=1))

    if len(clean_returns) < 2 or daily_volatility == 0:
        sharpe_ratio = float("nan")
    else:
        sharpe_ratio = float(
            excess_returns.mean() / daily_volatility * np.sqrt(periods_per_year)
        )

    wealth_with_initial_value = pd.concat(
        [
            pd.Series([1.0]),
            wealth.reset_index(drop=True),
        ],
        ignore_index=True,
    )

    running_peak = wealth_with_initial_value.cummax()
    drawdowns = wealth_with_initial_value / running_peak - 1.0
    maximum_drawdown = float(drawdowns.min())

    return {
        "total_return": total_return,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "sharpe_ratio": sharpe_ratio,
        "maximum_drawdown": maximum_drawdown,
    }


def compare_assets(
    returns: pd.DataFrame,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> pd.DataFrame:
    """Calculate performance metrics for each asset in a returns DataFrame.

    Missing observations are rejected rather than silently removed or
    replaced. Align and select the intended evaluation period beforehand.
    """

    if not isinstance(returns, pd.DataFrame):
        raise TypeError("Returns must be supplied as a pandas DataFrame.")

    if returns.empty or returns.shape[1] == 0:
        raise ValueError("Returns must contain at least one asset and one row.")

    if returns.columns.has_duplicates:
        raise ValueError("Returns contain duplicate asset columns.")

    if returns.isna().any().any():
        raise ValueError(
            "Returns contain missing observations. Select a common evaluation "
            "period or handle missing data explicitly before comparison."
        )

    metrics = {
        str(ticker): calculate_performance_metrics(
            returns[ticker],
            periods_per_year=periods_per_year,
            risk_free_rate=risk_free_rate,
        )
        for ticker in returns.columns
    }

    return pd.DataFrame.from_dict(metrics, orient="index").rename_axis("ticker")