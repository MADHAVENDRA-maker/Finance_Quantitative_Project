import pandas as pd
import streamlit as st
import plotly.express as px
from project_structure.stress_testing.engine import (calculate_stress_impact)

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


SCENARIOS = {
    "Equity Market Crash": {
        "SPY": -20, "QQQ": -25, "IWM": -25,
        "EFA": -20, "EEM": -25, "TLT": 5,
        "IEF": 2, "GLD": 5, "VNQ": -20, "DBC": -10,
    },
    "Inflation Shock": {
        "SPY": -10, "QQQ": -12, "IWM": -12,
        "EFA": -10, "EEM": -12, "TLT": -12,
        "IEF": -6, "GLD": 8, "VNQ": -8, "DBC": 15,
    },
    "Interest Rate Shock": {
        "SPY": -5, "QQQ": -8, "IWM": -5,
        "EFA": -5, "EEM": -6, "TLT": -15,
        "IEF": -7, "GLD": -2, "VNQ": -10, "DBC": -3,
    },
    "Custom Scenario": {},
}


def render_stress_testing_page(project_root):

    st.title("Portfolio Stress Testing")

    st.write(
        "Construct a portfolio and investigate how it could respond "
        "to hypothetical market shocks. Configure asset allocations, "
        "select a scenario, and analyse the resulting portfolio impact."
    )

    processed_dir = project_root / "data" / "processed"

    available_tickers = [
        ticker
        for ticker in ASSET_NAMES
        if (processed_dir / f"{ticker}.csv").exists()
    ]

    if not available_tickers:
        st.error(
            "No supported ETF market-data files were found in "
            f"{processed_dir}."
        )
        return

    # ---------------------------------------------------------
    # 1. PORTFOLIO CONFIGURATION
    # ---------------------------------------------------------

    st.divider()
    st.header("1. Build Your Portfolio")

    selected_tickers = st.multiselect(
        "Select assets for your portfolio",
        options=available_tickers,
        default=available_tickers,
        format_func=lambda ticker: (
            f"{ticker} — {ASSET_NAMES[ticker]}"
        ),
        max_selections=10,
        key="stress_selected_assets",
    )

    if not selected_tickers:
        st.info("Select at least one asset to continue.")
        return

    allocation_method = st.radio(
        "Portfolio weighting method",
        ["Equal Weight", "Custom Weights"],
        horizontal=True,
        key="stress_allocation_method",
    )

    if allocation_method == "Equal Weight":
        weights = pd.Series(
            1.0 / len(selected_tickers),
            index=selected_tickers,
            dtype=float,
        )

    else:
        st.caption(
            "Enter the target percentage allocation for each asset. "
            "The total must equal 100%."
        )

        weight_columns = st.columns(min(3, len(selected_tickers)))
        custom_weights = {}

        for i, ticker in enumerate(selected_tickers):
            with weight_columns[i % len(weight_columns)]:
                custom_weights[ticker] = st.number_input(
                    f"{ticker} weight (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=round(100.0 / len(selected_tickers), 4),
                    step=1.0,
                    key=f"stress_weight_{ticker}",
                )

        weights = pd.Series(
            custom_weights,
            dtype=float,
        ) / 100.0

        total_weight = float(weights.sum())

        if abs(total_weight - 1.0) > 0.0001:
            st.warning(
                f"Your portfolio allocations currently total "
                f"{total_weight * 100:.2f}%. They must total 100%."
            )
            return

    portfolio_value = st.number_input(
        "Initial Portfolio Value",
        min_value=1.0,
        value=1_000_000.0,
        step=100_000.0,
        key="stress_portfolio_value",
    )
    st.caption(
        f"Portfolio Value (USD): ${portfolio_value:,.2f}"
    )

    allocation_table = pd.DataFrame({
        "Ticker": selected_tickers,
        "Asset": [
            ASSET_NAMES[ticker] for ticker in selected_tickers
        ],
        "Portfolio Weight": [
            weights[ticker] * 100 for ticker in selected_tickers
        ],
    })

    st.subheader("Portfolio Allocation")

    st.dataframe(
        allocation_table.style.format({
            "Portfolio Weight": "{:.2f}%"
        }),
        hide_index=True,
        width="stretch",
    )

    # ---------------------------------------------------------
    # 2. SCENARIO CONFIGURATION
    # ---------------------------------------------------------

    st.divider()
    st.header("2. Configure Stress Scenario")

    scenario_name = st.selectbox(
        "Select a market scenario",
        list(SCENARIOS.keys()),
        key="stress_scenario",
    )

    default_shocks = SCENARIOS[scenario_name]

    shock_table = pd.DataFrame({
        "Asset": selected_tickers,
        "Asset Description": [
            ASSET_NAMES[ticker] for ticker in selected_tickers
        ],
        "Portfolio Weight (%)": [
            weights[ticker] * 100 for ticker in selected_tickers
        ],
        "Shock (%)": [
            default_shocks.get(ticker, 0.0)
            for ticker in selected_tickers
        ],
    })

    st.caption(
        "Adjust the assumed percentage change for each asset. "
        "Negative values represent declines and positive values "
        "represent gains."
    )

    edited_table = st.data_editor(
        shock_table,
        hide_index=True,
        width="stretch",
        disabled=[
            "Asset",
            "Asset Description",
            "Portfolio Weight (%)",
        ],
        column_config={
            "Portfolio Weight (%)": st.column_config.NumberColumn(
                format="%.2f%%"
            ),
            "Shock (%)": st.column_config.NumberColumn(
                min_value=-100.0,
                max_value=200.0,
                step=1.0,
                format="%.1f%%",
            ),
        },
        key=f"stress_shocks_{scenario_name}",
    )

    # ---------------------------------------------------------
    # 3. RUN STRESS TEST
    # ---------------------------------------------------------

    st.divider()

    run_clicked = st.button(
        "Run Stress Test",
        type="primary",
        width="stretch",
    )

    if run_clicked:

        shocks = pd.Series(
            edited_table["Shock (%)"].to_numpy(dtype=float) / 100.0,
            index=edited_table["Asset"].tolist(),
            dtype=float,
        )

        try:
            detail, summary = calculate_stress_impact(
                weights=weights,
                shocks=shocks,
                portfolio_value=float(portfolio_value),
            )

            st.session_state["independent_stress_results"] = {
                "scenario": scenario_name,
                "detail": detail,
                "summary": summary,
            }

        except (TypeError, ValueError) as exc:
            st.error(f"Stress test could not be completed: {exc}")
            return

    # ---------------------------------------------------------
    # 4. DISPLAY RESULTS
    # ---------------------------------------------------------

    saved_results = st.session_state.get(
        "independent_stress_results"
    )

    if not saved_results:
        st.info(
            "Configure your portfolio and scenario, then run "
            "the stress test to view the results."
        )
        return

    detail = saved_results["detail"]
    summary = saved_results["summary"]

    st.divider()
    st.header("3. Stress Test Results")

    st.caption(
        f"Scenario: {saved_results['scenario']}"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Portfolio Impact",
        f"{summary['portfolio_return']:.2%}",
    )

    col2.metric(
        "Estimated P&L",
        f"{summary['estimated_pnl']:,.2f}",
    )

    col3.metric(
        "Stressed Portfolio Value",
        f"{summary['stressed_value']:,.2f}",
    )

    st.subheader("Asset-Level Contributions")

    chart_data = detail.reset_index()

    chart_data["Contribution (%)"] = (
        chart_data["portfolio_contribution"] * 100
    )

    figure = px.bar(
        chart_data,
        x="asset",
        y="Contribution (%)",
        color="Contribution (%)",
        title="Contribution of Each Asset to Portfolio Impact",
    )

    figure.update_layout(
        xaxis_title="Asset",
        yaxis_title="Portfolio Return Contribution",
        height=420,
        showlegend=False,
    )

    st.plotly_chart(figure, width="stretch")

    st.subheader("Detailed Results")

    display_table = detail.rename(
        columns={
            "weight": "Portfolio Weight",
            "asset_shock": "Asset Shock",
            "portfolio_contribution": "Portfolio Contribution",
            "estimated_pnl": "Estimated P&L",
        }
    )

    st.dataframe(
        display_table.style.format({
            "Portfolio Weight": "{:.2%}",
            "Asset Shock": "{:.2%}",
            "Portfolio Contribution": "{:.2%}",
            "Estimated P&L": "{:,.2f}",
        }),
        width="stretch",
    )

    st.caption(
        "This is a deterministic scenario analysis based on "
        "user-specified asset shocks. It is not a forecast and "
        "does not currently model changing correlations, liquidity, "
        "or volatility."
    )