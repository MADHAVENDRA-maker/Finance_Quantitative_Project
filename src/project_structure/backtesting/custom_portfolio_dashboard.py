import json
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from project_structure.backtesting.custom_portfolio import (run_custom_portfolio_backtest)

ASSET_NAMES = {
    "SPY": "US Large-Cap Equities",
    "QQQ": "Nasdaq-100 Equities",
    "IWM": "US Small-Cap Equities",
    "EFA": "Developed International Equities",
    "EEM": "Emerging Markets Equities",
    "TLT": "Long-Term US Treasury Bonds",
    "IEF": "Intermediate-Term US Treasury Bonds",
    "GLD": "Gold",
    "VNQ": "US Real Estate",
    "DBC": "Commodities",
}


@st.cache_data(show_spinner=False)
def _load_adjusted_prices(csv_path: str,file_mtime_ns: int,file_size: int,) -> pd.Series:
    """Load adjusted closing prices from one processed asset CSV."""
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"Market-data file not found: {path.name}")

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(f"{path.name} contains no observations.")

    # Normalize column labels for reliable matching.
    original_columns = list(df.columns)
    normalized = {
        str(column).strip().lower().replace("_", " "): column
        for column in original_columns
    }

    date_column = next(
        (
            normalized[name]
            for name in ("date", "datetime", "timestamp")
            if name in normalized
        ),
        None,
    )

    # CSVs saved from a DataFrame index sometimes have an unnamed date column.
    if date_column is None:
        date_column = original_columns[0]

    adjusted_column = next(
        (
            normalized[name]
            for name in ("adj close", "adjusted close", "adjclose")
            if name in normalized
        ),
        None,
    )

    if adjusted_column is None:
        raise ValueError(
            f"{path.name} has no adjusted-close column. "
            "The custom backtest requires adjusted prices."
        )

    dates = pd.to_datetime(df[date_column], errors="coerce",utc=True).dt.tz_convert(None)
    prices = pd.to_numeric(df[adjusted_column], errors="coerce")

    result = pd.Series(prices.to_numpy(), index=dates, name=path.stem)
    result = result[~result.index.isna()]
    result = result[~result.index.duplicated(keep="last")]
    result = result.sort_index()
    result = result.dropna()

    if result.empty:
        raise ValueError(f"No valid adjusted prices found in {path.name}.")

    if (result <= 0).any():
        raise ValueError(f"{path.name} contains non-positive adjusted prices.")

    result.index = pd.DatetimeIndex(result.index)
    result.index.name = "Date"
    return result


def _load_universe_returns(
    processed_dir: Path,
    tickers: list[str],
) -> pd.DataFrame:
    """Load and align adjusted prices, then calculate simple daily returns."""
    prices = {}

    for ticker in tickers:
        path = processed_dir / f"{ticker}.csv"

        if not path.exists():
            raise FileNotFoundError(
                f"Market-data file not found: {path.name}"
            )

        file_stats = path.stat()

        prices[ticker] = _load_adjusted_prices(
            str(path),
            file_stats.st_mtime_ns,
            file_stats.st_size,
        )

    price_frame = pd.concat(prices, axis=1, join="inner")
    price_frame = price_frame.sort_index().dropna(how="any")

    if len(price_frame) < 3:
        raise ValueError(
            "The selected assets do not have enough overlapping price history."
        )

    returns = price_frame.pct_change(fill_method=None).dropna(how="any")
    returns = returns.replace([np.inf, -np.inf], np.nan).dropna(how="any")
    returns.index = pd.DatetimeIndex(returns.index)
    returns.index.name = "Date"

    return returns



def render_custom_portfolio_page(project_root: Path) -> None:
    """Render the custom portfolio builder and its backtest results."""
    st.title("Custom Portfolio Builder")
    st.write(
        "Build and backtest a long-only ETF portfolio using historical "
        "adjusted prices, configurable weights, a study window, and "
        "transaction costs."
    )

    processed_dir = project_root / "data" / "processed"

    available_tickers = [
        ticker
        for ticker in ASSET_NAMES
        if (processed_dir / f"{ticker}.csv").exists()
    ]

    if not available_tickers:
        st.error(
            f"No supported processed ETF CSV files were found in "
            f"`{processed_dir}`."
        )
        return

    selected_tickers = st.multiselect(
        "Select ETFs (choose between 1 and 10)",
        options=available_tickers,
        default=available_tickers,
        format_func=lambda ticker: f"{ticker} — {ASSET_NAMES[ticker]}",
        max_selections=10,
        key="custom_portfolio_tickers",
    )

    if not selected_tickers:
        st.info("Select at least one ETF to configure a portfolio.")
        return

    try:
        universe_returns = _load_universe_returns(
            processed_dir,
            selected_tickers,
        )
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        st.error(f"Could not load market data: {exc}")
        return

    earliest_date = universe_returns.index.min().date()
    latest_date = universe_returns.index.max().date()

    st.caption(
        f"Common available return history for the selected assets: "
        f"{earliest_date:%d %b %Y} to {latest_date:%d %b %Y}. "
        "The common history is used so that all selected assets are "
        "compared on the same dates."
    )

    # Keep allocation controls outside the form so they update immediately.
    st.subheader("Portfolio Allocation")

    allocation_method = st.radio(
        "Weighting method",
        options=["Equal weight", "Custom weights"],
        horizontal=True,
        key="custom_portfolio_allocation_method",
    )

    custom_percentages = {}

    if allocation_method == "Custom weights":
        st.caption(
            "Enter each selected ETF's target allocation. "
            "The total must equal 100%."
        )

        columns = st.columns(min(3, len(selected_tickers)))

        for index, ticker in enumerate(selected_tickers):
            default_pct = 100.0 / len(selected_tickers)

            with columns[index % len(columns)]:
                custom_percentages[ticker] = st.number_input(
                    f"{ticker} allocation (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=round(default_pct, 4),
                    step=1.0,
                    key=f"custom_weight_{ticker}",
                )

    # Keep the remaining settings and submit button inside the form.
    with st.form("custom_portfolio_settings"):
        st.subheader("Study and Backtest Settings")

        lookback = st.number_input(
            "Lookback window (trading days)",
            min_value=2,
            max_value=1000,
            value=252,
            step=1,
            help=(
                "Number of historical daily return observations used before "
                "the first evaluated return. The fixed-weight strategy does "
                "not optimize weights from this history."
            ),
        )

        # The backtest needs `lookback` complete return observations before
        # the selected study start. Set the earliest selectable start date
        # accordingly, rather than allowing dates that cannot be backtested.
        lookback_days = int(lookback)
        min_start_position = min(lookback_days, len(universe_returns) - 1)
        min_date = universe_returns.index[min_start_position].date()
        max_date = latest_date

        # Keep the default window at approximately one year, or at least as
        # far forward as required by the selected lookback.
        default_start_position = min(
            max(252, lookback_days),
            len(universe_returns) - 1,
        )
        default_start = universe_returns.index[
            default_start_position
        ].date()

        # A data-range-specific key prevents Streamlit from reusing a
        # previously selected date that falls outside the current data range.
        study_window_key = (
            f"custom_portfolio_study_window_"
            f"{min_date.isoformat()}_{max_date.isoformat()}"
        )

        selected_dates = st.date_input(
            "Study window",
            value=(default_start, max_date),
            min_value=min_date,
            max_value=max_date,
            key=study_window_key,
            help=(
                "The backtest evaluates returns within this window. "
                f"At least {lookback_days} historical return observations "
                "must be available before the start date. The end date "
                "cannot exceed the latest date in the selected assets' "
                "common market-data history."
            ),
        )

        rebalance_every = st.number_input(
            "Rebalance interval (trading days)",
            min_value=1,
            max_value=252,
            value=21,
            step=1,
        )

        transaction_cost_bps = st.number_input(
            "Transaction cost (basis points per unit of turnover)",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=1.0,
            help=(
                "10 basis points = 0.10%. The existing engine applies "
                "the cost at initial portfolio establishment and each "
                "scheduled rebalance."
            ),
        )

        run_clicked = st.form_submit_button(
            "Run Custom Backtest",
            type="primary",
            width="stretch",
        )

    if not run_clicked:
        st.info(
            "Configure the portfolio and study window, then select "
            "**Run Custom Backtest**."
        )
        return

    if len(selected_dates) != 2:
        st.error("Select both a start date and an end date.")
        return

    start_date = pd.Timestamp(selected_dates[0])
    end_date = pd.Timestamp(selected_dates[1])

    if start_date > end_date:
        st.error("The study start date must not be after the end date.")
        return

    if allocation_method == "Equal weight":
        target_weights = pd.Series(
            1.0 / len(selected_tickers),
            index=selected_tickers,
            dtype=float,
        )
    else:
        percentage_total = sum(custom_percentages.values())

        if not np.isclose(
            percentage_total, 100.0, atol=0.01, rtol=0.0
        ):
            st.error(
                f"Custom allocations currently total "
                f"{percentage_total:.4f}%. "
                "Adjust them so the total equals 100%."
            )
            return

        target_weights = pd.Series(
            custom_percentages,
            dtype=float,
        ) / percentage_total

    # Use only observations strictly before the selected start date
    # to satisfy the lookback; evaluate returns inside the selected window.
    pre_start_history = universe_returns.loc[
        universe_returns.index < start_date
    ].tail(int(lookback))

    evaluation_returns = universe_returns.loc[
        (universe_returns.index >= start_date)
        & (universe_returns.index <= end_date)
    ]

    if len(pre_start_history) < int(lookback):
        st.error(
            f"Only {len(pre_start_history)} historical return observations "
            f"are available before {start_date:%d %b %Y}, but the selected "
            f"lookback requires {int(lookback)}. Choose a later start date "
            "or reduce the lookback. This avoids using incomplete history."
        )
        return

    if evaluation_returns.empty:
        st.error(
            "No market-return observations fall inside the selected study "
            "window. Choose a wider window or different dates."
        )
        return

    backtest_input = pd.concat(
        [pre_start_history, evaluation_returns],
        axis=0,
    )
    backtest_input = backtest_input.loc[:, selected_tickers]

    try:
        results, metrics, drawdown = run_custom_portfolio_backtest(
            asset_returns=backtest_input,
            weights=target_weights,
            lookback=int(lookback),
            rebalance_every=int(rebalance_every),
            transaction_cost_bps=float(transaction_cost_bps),
        )
    except (TypeError, ValueError, KeyError) as exc:
        st.error(f"The custom backtest could not be completed: {exc}")
        return

    if results.empty:
        st.error("The backtest returned no out-of-sample observations.")
        return
    st.session_state["stress_portfolio"] = {
        "assets": list(selected_tickers),
        "weights": {
            ticker: float(weight)
            for ticker, weight in target_weights.items()
        },
        "backtest_end_date": results.index.max().date().isoformat(),
    }

    results = results.copy()
    results["cumulative_return"] = (
        (1.0 + results["net_return"]).cumprod() - 1.0
    )
    results["drawdown"] = drawdown.reindex(results.index)

    st.success(
        f"Backtest completed: {results.index.min():%d %b %Y} to "
        f"{results.index.max():%d %b %Y} "
        f"({len(results):,} out-of-sample observations)."
    )

    if results.index.min().date() > start_date.date():
        st.warning(
            "The first evaluated trading day is later than the selected "
            "calendar start date because market returns are available only "
            "on trading days."
        )

    st.subheader("Performance Summary")

    metric_columns = st.columns(3)
    metric_columns[0].metric(
        "Total Return", f"{metrics['total_return']:.2%}"
    )
    metric_columns[1].metric(
        "Annualized Return", f"{metrics['annualized_return']:.2%}"
    )
    metric_columns[2].metric(
        "Annualized Volatility",
        f"{metrics['annualized_volatility']:.2%}",
    )

    extra_metric_columns = st.columns(3)
    extra_metric_columns[0].metric(
        "Sharpe Ratio", f"{metrics['sharpe_ratio']:.3f}"
    )
    extra_metric_columns[1].metric(
        "Maximum Drawdown", f"{metrics['maximum_drawdown']:.2%}"
    )
    extra_metric_columns[2].metric(
        "Average Turnover", f"{metrics['average_turnover']:.3f}"
    )

    extra_columns = st.columns(3)
    extra_columns[0].metric(
        "Total Turnover", f"{metrics['total_turnover']:.3f}"
    )
    extra_columns[1].metric(
        "Rebalance Interval", f"{int(rebalance_every)} days"
    )
    extra_columns[2].metric(
        "Transaction Cost", f"{transaction_cost_bps:g} bps"
    )

    st.subheader("Cumulative Net Returns")

    cumulative_figure = go.Figure()
    cumulative_figure.add_trace(
        go.Scatter(
            x=results.index,
            y=results["cumulative_return"],
            mode="lines",
            name="Custom portfolio",
        )
    )
    cumulative_figure.update_layout(
        xaxis_title="Date",
        yaxis_title="Cumulative return",
        yaxis_tickformat=".0%",
        hovermode="x unified",
        height=420,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    st.plotly_chart(cumulative_figure, width="stretch")

    st.subheader("Drawdown")

    drawdown_figure = go.Figure()
    drawdown_figure.add_trace(
        go.Scatter(
            x=results.index,
            y=results["drawdown"],
            mode="lines",
            fill="tozeroy",
            name="Drawdown",
        )
    )
    drawdown_figure.update_layout(
        xaxis_title="Date",
        yaxis_title="Drawdown",
        yaxis_tickformat=".0%",
        hovermode="x unified",
        height=320,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    st.plotly_chart(drawdown_figure, width="stretch")

    st.subheader("Portfolio Weight History")

    weight_columns = [
        column
        for column in results.columns
        if column.startswith("weight_")
    ]

    weight_figure = go.Figure()

    for column in weight_columns:
        weight_figure.add_trace(
            go.Scatter(
                x=results.index,
                y=results[column],
                mode="lines",
                stackgroup="weights",
                name=column.removeprefix("weight_"),
            )
        )

    weight_figure.update_layout(
        xaxis_title="Date",
        yaxis_title="Portfolio weight",
        yaxis_tickformat=".0%",
        yaxis_range=[0, 1],
        hovermode="x unified",
        height=420,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    st.plotly_chart(weight_figure, width="stretch")

    st.subheader("Target Allocation")

    allocation_table = pd.DataFrame(
        {
            "Ticker": target_weights.index,
            "Target Weight": target_weights.values,
            "Asset Class": [
                ASSET_NAMES[ticker] for ticker in target_weights.index
            ],
        }
    )
    st.dataframe(
        allocation_table.style.format({"Target Weight": "{:.2%}"}),
        hide_index=True,
        width="stretch",
    )

    st.subheader("Backtest Results")

    st.dataframe(
        results.tail(500).style.format(
            {
                "gross_return": "{:.4%}",
                "net_return": "{:.4%}",
                "transaction_cost": "{:.4%}",
                "cumulative_return": "{:.2%}",
                "drawdown": "{:.2%}",
                "turnover": "{:.4f}",
                **{column: "{:.2%}" for column in weight_columns},
            }
        ),
        width="stretch",
    )

    configuration = {
        "selected_assets": selected_tickers,
        "study_start_date": start_date.date().isoformat(),
        "study_end_date": end_date.date().isoformat(),
        "actual_evaluation_start": results.index.min().date().isoformat(),
        "actual_evaluation_end": results.index.max().date().isoformat(),
        "allocation_method": allocation_method,
        "target_weights": {
            ticker: float(weight)
            for ticker, weight in target_weights.items()
        },
        "lookback_trading_days": int(lookback),
        "rebalance_every_trading_days": int(rebalance_every),
        "transaction_cost_bps": float(transaction_cost_bps),
        "observations": int(len(results)),
        "metrics": {
            key: value
            for key, value in metrics.items()
        },
    }

    st.subheader("Export")

    csv_bytes = results.to_csv(
        index=True, index_label="Date"
    ).encode("utf-8")

    json_bytes = json.dumps(
        configuration,
        indent=2,
        default=str,
    ).encode("utf-8")

    export_columns = st.columns(2)

    export_columns[0].download_button(
        "Download Backtest Results (CSV)",
        data=csv_bytes,
        file_name="custom_portfolio_backtest.csv",
        mime="text/csv",
        width="stretch",
    )

    export_columns[1].download_button(
        "Download Portfolio Configuration (JSON)",
        data=json_bytes,
        file_name="custom_portfolio_configuration.json",
        mime="application/json",
        width="stretch",
    )