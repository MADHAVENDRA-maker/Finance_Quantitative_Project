import streamlit as st


def render_overview_page(project_root):

    # ---------------------------------------------------------
    # PAGE HEADER
    # ---------------------------------------------------------

    st.title("FinSight - Quantitative Finance Research Platform")

    st.markdown(
        """
        An interactive environment for exploring portfolio construction,
        quantitative investment strategies, and financial risk.

        The platform combines historical market data, portfolio analytics,
        and scenario-based analysis to help users understand how investment
        decisions influence portfolio performance and risk.
        """
    )

    st.divider()

    # ---------------------------------------------------------
    # PLATFORM OVERVIEW
    # ---------------------------------------------------------

    st.subheader("Explore the Platform")

    st.markdown(
        """
        The platform provides a collection of quantitative tools designed
        to examine investment portfolios from different perspectives.
        Whether you are experimenting with asset allocations or evaluating
        portfolio resilience under adverse market conditions, each feature
        offers an analytical approach to understanding portfolio behaviour.
        """
    )

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("Custom Portfolio Builder")
            st.markdown(
                """
                Construct and analyse portfolios using a selection of
                exchange-traded funds (ETFs).

                - Select assets from the available investment universe.
                - Define equal-weighted or custom allocations.
                - Configure backtesting parameters.
                - Examine portfolio returns, drawdowns, and allocation
                  behaviour over time.
                """
            )

    with col2:
        with st.container(border=True):
            st.subheader("Portfolio Stress Testing")
            st.markdown(
                """
                Evaluate how a portfolio may respond to hypothetical
                adverse market conditions.

                - Construct an independent custom portfolio.
                - Allocate weights across selected assets.
                - Apply predefined or user-defined market shocks.
                - Analyse estimated portfolio losses and asset-level
                  contributions under various scenarios.
                """
            )

    # ---------------------------------------------------------
    # RESEARCH FRAMEWORK
    # ---------------------------------------------------------

    st.divider()

    st.subheader("The Quantitative Research Framework")

    st.markdown(
        """
        Beyond individual tools, the broader research project focuses
        on understanding the key components of quantitative portfolio
        management.
        """
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Portfolio Construction")
        st.markdown(
            """
            Explore how asset selection, allocation weights, and
            diversification influence the overall characteristics
            of an investment portfolio.
            """
        )

    with col2:
        st.markdown("#### Performance Analysis")
        st.markdown(
            """
            Examine historical returns, volatility, risk-adjusted
            performance, and drawdowns to evaluate investment
            strategies.
            """
        )

    with col3:
        st.markdown("#### Risk Assessment")
        st.markdown(
            """
            Investigate portfolio sensitivity to market movements
            and understand how different assets contribute to
            overall portfolio risk.
            """
        )

    # ---------------------------------------------------------
    # GETTING STARTED
    # ---------------------------------------------------------

    st.divider()

    st.subheader("Getting Started")

    st.markdown(
        """
        Follow these steps to begin exploring the platform:
        """
    )

    st.markdown(
        """
        1. **Open Custom Portfolio Builder** from the sidebar to
           construct your investment portfolio.

        2. **Configure your allocations** by selecting assets and
           assigning portfolio weights.

        3. **Run the analysis** to examine historical portfolio
           performance and risk characteristics.

        4. **Explore Portfolio Stress Testing** to investigate how
           your allocation may respond to different hypothetical
           market scenarios.
        """
    )

    st.info(
        "Tip: Start with the Custom Portfolio Builder to understand "
        "portfolio construction, then use Portfolio Stress Testing "
        "to explore the potential impact of adverse market conditions."
    )

    # ---------------------------------------------------------
    # DISCLAIMER
    # ---------------------------------------------------------

    st.divider()

    st.caption(
        """
        **Research Disclaimer:** This platform is developed for
        educational, quantitative research, and analytical purposes.
        Historical performance and hypothetical stress-test results
        do not guarantee future outcomes. The analyses presented
        should not be interpreted as investment advice.
        """
    )