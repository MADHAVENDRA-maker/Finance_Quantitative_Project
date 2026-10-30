from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from project_structure.backtesting.custom_portfolio_dashboard import (render_custom_portfolio_page)
from project_structure.dashboard.overview import render_overview_page
from project_structure.stress_testing.dashboard import (render_stress_testing_page)

PROJECT_ROOT = Path(__file__).resolve().parent
RUNS_DIR = PROJECT_ROOT / "data" / "runs"

STRATEGY_FILES = {
    "Equal Weight": RUNS_DIR / "backtest_equal_weight.csv",
    "Minimum Variance": RUNS_DIR / "backtest_minimum_variance.csv",
    "Maximum Sharpe": RUNS_DIR / "backtest_maximum_sharpe.csv",
}

st.set_page_config(
    page_title="Quantitative Finance Research",
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

pages = [
    "Overview",
    "Custom Portfolio Builder",
    "Portfolio Stress Testing",
]

page = st.sidebar.radio(
    "Navigation",
    pages,
)

st.sidebar.divider()
st.sidebar.caption("Historical research results — not investment advice.")


# ---------------------------------------------------------
# Overview
# ---------------------------------------------------------

if page == "Overview":
    render_overview_page(PROJECT_ROOT)

# ---------------------------------------------------------
# Custom portfolio builder
# ---------------------------------------------------------

elif page == "Custom Portfolio Builder":
    render_custom_portfolio_page(PROJECT_ROOT)


# ---------------------------------------------------------
# Custom portfolio builder
# ---------------------------------------------------------

elif page == "Portfolio Stress Testing":
    render_stress_testing_page(PROJECT_ROOT)