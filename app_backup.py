from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from project_structure.backtesting.custom_portfolio_dashboard import (render_custom_portfolio_page)

PROJECT_ROOT = Path(__file__).resolve().parent
RUNS_DIR = PROJECT_ROOT / "data" / "runs"

STRATEGY_FILES = {
    "Equal Weight": RUNS_DIR / "backtest_equal_weight.csv",
    "Minimum Variance": RUNS_DIR / "backtest_minimum_variance.csv",
    "Maximum Sharpe": RUNS_DIR / "backtest_maximum_sharpe.csv",
}

st.set_page_config(
    page_title="Quantitative Finance Research",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.07);
        border: 1px solid rgba(128, 128, 128, 0.15);
        padding: 12px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Data loading
# ---------------------------------------------------------

@st.cache_data
def load_csv(path_string):
    """Load a CSV if it exists; cache until the app is refreshed."""
    path = Path(path_string)

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)


def load_run_file(relative_path):
    return load_csv(str(RUNS_DIR / relative_path))


def load_strategy_file(strategy):
    path = STRATEGY_FILES.get(strategy)

    if path is None or not path.exists():
        return pd.DataFrame()

    return load_csv(str(path))


def clean_columns(df):
    """Normalize CSV column names and remove exported index columns."""
    if df.empty:
        return df

    result = df.copy()
    result.columns = [str(c).strip().lower() for c in result.columns]

    unwanted = [
        c for c in result.columns
        if c.startswith("unnamed:")
    ]

    if unwanted:
        result = result.drop(columns=unwanted)

    return result


def find_column(df, candidates):
    """Find the first matching column from a list of alternatives."""
    if df.empty:
        return None

    columns = {str(c).lower(): c for c in df.columns}

    for candidate in candidates:
        if candidate.lower() in columns:
            return columns[candidate.lower()]

    return None


def parse_dates(df):
    """Convert a recognized date column to datetime."""
    if df.empty:
        return df

    result = df.copy()
    date_col = find_column(
        result,
        ["date", "datetime", "timestamp", "time", "index"],
    )

    if date_col:
        result[date_col] = pd.to_datetime(
            result[date_col], errors="coerce"
        )
        result = result.dropna(subset=[date_col])
        result = result.sort_values(date_col)

    return result


def number(value, percent=False, decimals=2):
    if pd.isna(value):
        return "N/A"

    if percent:
        return f"{value:.{decimals}%}"

    return f"{value:,.{decimals}f}"


def metric_value(row, candidates):
    col = find_column(pd.DataFrame([row]), candidates)

    if col is None:
        return np.nan

    return pd.to_numeric(row[col], errors="coerce")


def show_missing(message):
    st.info(message)


def show_dataframe(df, height=350):
    if df.empty:
        show_missing("No saved results were found for this section.")
        return

    st.dataframe(df, width="stretch", height=height)


# ---------------------------------------------------------
# Common chart helpers
# ---------------------------------------------------------

def cumulative_return_series(df):
    """
    Return a cumulative-return series from a saved backtest.

    Prefer a stored cumulative series. Otherwise, compound
    the daily net-return series.
    """
    if df.empty:
        return None, None

    data = parse_dates(clean_columns(df))

    date_col = find_column(
        data, ["date", "datetime", "timestamp", "time", "index"]
    )

    cumulative_col = find_column(
        data,
        ["cumulative_return", "cumulative_returns",
         "portfolio_cumulative_return", "wealth"],
    )

    return_col = find_column(
        data,
        ["net_return", "portfolio_return", "strategy_return",
         "daily_return", "returns"],
    )

    if date_col is None:
        return None, None

    if cumulative_col is not None:
        values = pd.to_numeric(data[cumulative_col], errors="coerce")
        return data[date_col], values

    if return_col is not None:
        returns = pd.to_numeric(data[return_col], errors="coerce")
        values = (1 + returns.fillna(0)).cumprod() - 1
        return data[date_col], values

    return None, None


def cumulative_returns_chart(strategy_names):
    fig = go.Figure()
    added = 0

    for strategy in strategy_names:
        df = load_strategy_file(strategy)
        dates, values = cumulative_return_series(df)

        if dates is None or values is None:
            continue

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode="lines",
                name=strategy,
            )
        )
        added += 1

    if added == 0:
        return None

    fig.update_layout(
        title="Cumulative Returns",
        xaxis_title="Date",
        yaxis_title="Cumulative return",
        yaxis_tickformat=".0%",
        hovermode="x unified",
        legend_title="Strategy",
        height=460,
        margin=dict(l=10, r=10, t=60, b=10),
    )

    return fig


def comparison_bar_chart(df, metric, title, percent=False):
    metric_col = find_column(df, [metric])
    strategy_col = find_column(df, ["strategy"])

    if metric_col is None or strategy_col is None:
        return None

    chart_df = df[[strategy_col, metric_col]].copy()
    chart_df[metric_col] = pd.to_numeric(
        chart_df[metric_col], errors="coerce"
    )
    chart_df = chart_df.dropna()

    if chart_df.empty:
        return None

    fig = px.bar(
        chart_df,
        x=strategy_col,
        y=metric_col,
        title=title,
        text=metric_col,
    )

    fig.update_traces(
        texttemplate="%{y:.2%}" if percent else "%{y:.3f}",
        textposition="outside",
    )
    fig.update_layout(
        showlegend=False,
        height=360,
        margin=dict(l=10, r=10, t=60, b=10),
    )

    return fig


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

st.sidebar.title("Research Platform")
st.sidebar.caption("Quantitative Finance Analytics")

page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Backtesting",
        "Custom Portfolio Builder",
        "Robustness Analysis",
        "Walk-Forward Validation",
        "Data & Diagnostics",
    ],
)

st.sidebar.divider()
st.sidebar.caption("Historical research results — not investment advice.")


# ---------------------------------------------------------
# Overview
# ---------------------------------------------------------

if page == "Overview":
    st.title("Quantitative Finance Research Platform")
    st.markdown(
        "Explore portfolio performance, risk, robustness, "
        "and walk-forward validation from saved experiments."
    )

    comparison = clean_columns(
        load_run_file("backtest_comparison.csv")
    )

    if comparison.empty:
        show_missing(
            "The baseline comparison file is missing. "
            "Check data/runs/backtest_comparison.csv."
        )
    else:
        strategy_col = find_column(comparison, ["strategy"])
        sharpe_col = find_column(comparison, ["sharpe_ratio"])
        cagr_col = find_column(
            comparison, ["annualized_return"]
        )
        vol_col = find_column(
            comparison, ["annualized_volatility"]
        )
        dd_col = find_column(
            comparison, ["maximum_drawdown"]
        )
        start_col = find_column(comparison, ["start_date"])
        end_col = find_column(comparison, ["end_date"])

        if strategy_col and sharpe_col:
            selected_strategy = st.selectbox(
                "Strategy for key metrics",
                comparison[strategy_col].tolist(),
            )

            selected = comparison[
                comparison[strategy_col] == selected_strategy
            ].iloc[0]

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Annualized Return",
                number(
                    pd.to_numeric(selected[cagr_col], errors="coerce"),
                    percent=True,
                ) if cagr_col else "N/A",
            )
            c2.metric(
                "Annualized Volatility",
                number(
                    pd.to_numeric(selected[vol_col], errors="coerce"),
                    percent=True,
                ) if vol_col else "N/A",
            )
            c3.metric(
                "Sharpe Ratio",
                number(
                    pd.to_numeric(selected[sharpe_col], errors="coerce")
                ),
            )
            c4.metric(
                "Maximum Drawdown",
                number(
                    pd.to_numeric(selected[dd_col], errors="coerce"),
                    percent=True,
                ) if dd_col else "N/A",
            )

            if start_col and end_col:
                st.caption(
                    f"Baseline evaluation period: "
                    f"{selected[start_col]} to {selected[end_col]}. "
                    "Metrics use the saved baseline experiment."
                )

        st.subheader("Baseline Strategy Comparison")
        show_dataframe(comparison)

        fig = cumulative_returns_chart(list(STRATEGY_FILES.keys()))

        if fig is not None:
            st.plotly_chart(fig, width="stretch")
        else:
            show_missing(
                "Cumulative-return columns could not be identified "
                "in the saved strategy files. We'll adapt the loader "
                "after inspecting their headers."
            )

        left, right = st.columns(2)

        with left:
            fig = comparison_bar_chart(
                comparison,
                "sharpe_ratio",
                "Sharpe Ratio by Strategy",
            )
            if fig is not None:
                st.plotly_chart(fig, width="stretch")

        with right:
            fig = comparison_bar_chart(
                comparison,
                "maximum_drawdown",
                "Maximum Drawdown by Strategy",
                percent=True,
            )
            if fig is not None:
                st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------
# Backtesting
# ---------------------------------------------------------

elif page == "Backtesting":
    st.title("Backtesting Explorer")
    st.write(
        "Inspect saved strategy-level results and compare portfolio "
        "performance. This page does not run a new backtest."
    )

    comparison = clean_columns(
        load_run_file("backtest_comparison.csv")
    )

    if comparison.empty:
        show_missing("Baseline backtest comparison is unavailable.")
    else:
        st.subheader("Performance Summary")
        show_dataframe(comparison)

        available = [
            name for name, path in STRATEGY_FILES.items()
            if path.exists()
        ]

        if available:
            chosen = st.multiselect(
                "Strategies to plot",
                available,
                default=available,
            )

            fig = cumulative_returns_chart(chosen)

            if fig is not None:
                st.plotly_chart(fig, width="stretch")

            strategy = st.selectbox(
                "Inspect a saved strategy file",
                available,
            )
            df = parse_dates(
                clean_columns(load_strategy_file(strategy))
            )

            st.subheader(f"{strategy}: Saved Backtest Series")

            if not df.empty:
                date_col = find_column(
                    df, ["date", "datetime", "timestamp", "time", "index"]
                )

                numeric_cols = [
                    c for c in df.columns
                    if pd.api.types.is_numeric_dtype(df[c])
                ]

                if numeric_cols:
                    selected_metric = st.selectbox(
                        "Series to inspect",
                        numeric_cols,
                        index=(
                            numeric_cols.index(
                                find_column(
                                    df,
                                    ["drawdown", "net_return",
                                     "cumulative_return"],
                                )
                            )
                            if find_column(
                                df,
                                ["drawdown", "net_return",
                                 "cumulative_return"],
                            ) in numeric_cols
                            else 0
                        ),
                    )

                    if date_col:
                        fig = px.line(
                            df,
                            x=date_col,
                            y=selected_metric,
                            title=f"{strategy} — {selected_metric}",
                        )
                        st.plotly_chart(
                            fig, width="stretch"
                        )

                st.caption(
                    "Raw saved rows are shown below for transparency."
                )
                show_dataframe(df.tail(500))
            else:
                show_missing("The selected strategy file is empty.")
        else:
            show_missing("No individual baseline backtest files found.")

# ---------------------------------------------------------
# Custom portfolio builder
# ---------------------------------------------------------

elif page == "Custom Portfolio Builder":
    render_custom_portfolio_page(PROJECT_ROOT)


# ---------------------------------------------------------
# Robustness analysis
# ---------------------------------------------------------

elif page == "Robustness Analysis":
    st.title("Robustness Analysis")
    st.write(
        "Compare strategies across the tested rebalancing intervals "
        "and transaction-cost assumptions."
    )

    df = clean_columns(
        load_run_file("robustness/robustness_comparison.csv")
    )

    if df.empty:
        show_missing("Robustness results are unavailable.")
    else:
        strategy_col = find_column(df, ["strategy"])
        interval_col = find_column(
            df, ["rebalance_every", "rebalance_interval"]
        )
        cost_col = find_column(
            df, ["transaction_cost_bps", "cost_bps"]
        )
        sharpe_col = find_column(df, ["sharpe_ratio"])

        filtered = df.copy()

        if strategy_col:
            options = sorted(filtered[strategy_col].dropna().unique())
            chosen = st.multiselect(
                "Strategies",
                options,
                default=options,
            )
            filtered = filtered[
                filtered[strategy_col].isin(chosen)
            ]

        if interval_col:
            intervals = sorted(
                pd.to_numeric(
                    filtered[interval_col], errors="coerce"
                ).dropna().unique()
            )
            chosen_intervals = st.multiselect(
                "Rebalance interval (trading days)",
                intervals,
                default=intervals,
            )
            filtered = filtered[
                pd.to_numeric(
                    filtered[interval_col], errors="coerce"
                ).isin(chosen_intervals)
            ]

        if cost_col:
            costs = sorted(
                pd.to_numeric(
                    filtered[cost_col], errors="coerce"
                ).dropna().unique()
            )
            chosen_costs = st.multiselect(
                "Transaction cost (bps)",
                costs,
                default=costs,
            )
            filtered = filtered[
                pd.to_numeric(
                    filtered[cost_col], errors="coerce"
                ).isin(chosen_costs)
            ]

        st.subheader("Filtered Configurations")
        show_dataframe(filtered)

        if sharpe_col and strategy_col and not filtered.empty:
            plot_df = filtered.copy()
            plot_df[sharpe_col] = pd.to_numeric(
                plot_df[sharpe_col], errors="coerce"
            )

            label_cols = [strategy_col]
            if interval_col:
                label_cols.append(interval_col)
            if cost_col:
                label_cols.append(cost_col)

            plot_df["configuration"] = plot_df[
                label_cols
            ].astype(str).agg(" | ".join, axis=1)

            fig = px.bar(
                plot_df.sort_values(sharpe_col),
                x=sharpe_col,
                y="configuration",
                orientation="h",
                title="Sharpe Ratio by Configuration",
            )
            fig.update_layout(height=max(400, len(plot_df) * 28))
            st.plotly_chart(fig, width="stretch")

        cost_sensitivity = clean_columns(
            load_run_file(
                "robustness/transaction_cost_sensitivity.csv"
            )
        )

        st.subheader("Transaction-Cost Sensitivity")
        show_dataframe(cost_sensitivity)


# ---------------------------------------------------------
# Walk-forward validation
# ---------------------------------------------------------

elif page == "Walk-Forward Validation":
    st.title("Walk-Forward Validation")
    st.write(
        "Review historical-only schedule selection, fixed-versus-adaptive "
        "results, and stateful portfolio simulation."
    )

    tabs = st.tabs(
        [
            "Expanding Walk-Forward",
            "Stateful Walk-Forward",
            "Fixed vs Adaptive",
        ]
    )

    with tabs[0]:
        st.subheader("Expanding Walk-Forward")
        decisions = clean_columns(
            load_run_file("walk_forward/walk_forward_decisions.csv")
        )
        summary = clean_columns(
            load_run_file("walk_forward/walk_forward_summary.csv")
        )

        st.markdown("**Performance summary**")
        show_dataframe(summary)

        st.markdown("**Yearly schedule decisions**")
        show_dataframe(decisions)

        chart_path = (
            RUNS_DIR / "walk_forward"
            / "walk_forward_cumulative_returns.png"
        )
        if chart_path.exists():
            st.image(
                str(chart_path),
                caption="Saved expanding walk-forward cumulative returns",
                width="stretch",
            )

    with tabs[1]:
        st.subheader("Stateful Walk-Forward")
        summary = clean_columns(
            load_run_file(
                "walk_forward_stateful/stateful_walk_forward_summary.csv"
            )
        )
        decisions = clean_columns(
            load_run_file(
                "walk_forward_stateful/stateful_walk_forward_decisions.csv"
            )
        )

        st.markdown("**Performance summary**")
        show_dataframe(summary)

        st.markdown("**Yearly schedule decisions**")
        show_dataframe(decisions)

        chart_path = (
            RUNS_DIR / "walk_forward_stateful"
            / "stateful_walk_forward_cumulative_returns.png"
        )
        if chart_path.exists():
            st.image(
                str(chart_path),
                caption="Saved stateful walk-forward cumulative returns",
                width="stretch",
            )

    with tabs[2]:
        st.subheader("Fixed vs Adaptive Rebalancing")
        summary = clean_columns(
            load_run_file(
                "walk_forward_comparison/fixed_vs_adaptive_summary.csv"
            )
        )

        show_dataframe(summary)

        if not summary.empty:
            sharpe_col = find_column(summary, ["sharpe_ratio"])
            strategy_col = find_column(summary, ["strategy"])
            approach_col = find_column(summary, ["approach"])

            if sharpe_col and strategy_col and approach_col:
                plot_df = summary.copy()
                plot_df[sharpe_col] = pd.to_numeric(
                    plot_df[sharpe_col], errors="coerce"
                )
                plot_df["label"] = (
                    plot_df[strategy_col].astype(str)
                    + " — "
                    + plot_df[approach_col].astype(str)
                )

                fig = px.bar(
                    plot_df,
                    x="label",
                    y=sharpe_col,
                    title="Sharpe Ratio: Fixed vs Adaptive",
                )
                fig.update_layout(
                    xaxis_tickangle=-35,
                    height=480,
                )
                st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------
# Data and diagnostics
# ---------------------------------------------------------

elif page == "Data & Diagnostics":
    st.title("Data & Experiment Diagnostics")

    st.write(
        "This page reports which saved experiment files are present. "
        "It does not refresh market data or rerun analyses."
    )

    expected_files = [
        "backtest_comparison.csv",
        "backtest_equal_weight.csv",
        "backtest_minimum_variance.csv",
        "backtest_maximum_sharpe.csv",
        "portfolio_comparison.csv",
        "robustness/robustness_comparison.csv",
        "robustness/transaction_cost_sensitivity.csv",
        "walk_forward/walk_forward_summary.csv",
        "walk_forward/walk_forward_decisions.csv",
        "walk_forward_stateful/stateful_walk_forward_summary.csv",
        "walk_forward_stateful/stateful_walk_forward_decisions.csv",
        "walk_forward_comparison/fixed_vs_adaptive_summary.csv",
    ]

    diagnostics = []

    for relative_path in expected_files:
        path = RUNS_DIR / relative_path
        exists = path.exists()

        diagnostics.append(
            {
                "File": relative_path,
                "Available": "Yes" if exists else "No",
                "Size (KB)": (
                    round(path.stat().st_size / 1024, 1)
                    if exists else np.nan
                ),
                "Last modified": (
                    pd.Timestamp(
                        path.stat().st_mtime, unit="s"
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    if exists else "—"
                ),
            }
        )

    diagnostics_df = pd.DataFrame(diagnostics)
    show_dataframe(diagnostics_df, height=450)

    st.caption(
        "The dashboard uses saved CSVs and charts. "
        "Refresh the browser or clear Streamlit's cache after "
        "regenerating results outside the dashboard."
    )


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.sidebar.divider()
st.sidebar.caption("Research build • ML not included")