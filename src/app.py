import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from components.graphs import (
    plot_training_load_index,
    plot_metrics,
    plot_hr_zone_ranges,
)
from utils.calculations import (
    fetch_oura_data,
    calculate_training_load_index,
    adaptive_karvonen_zone_bounds,
    fetch_user_max_hr,
    fetch_user_resting_hr
)
from utils.oauth import get_authorization_url, fetch_access_token
import streamlit.components.v1 as components  # <--- import added here for JS snippet

def main():
    # Set page configuration
    st.set_page_config(
        page_title="Oura Training Dashboard",
        page_icon="🌙",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        "<h1 style='text-align: center; color: white;'>Oura Training Dashboard</h1>",
        unsafe_allow_html=True,
    )

    # Initialize session state variables
    if "access_token" not in st.session_state:
        st.session_state["access_token"] = None

    # Step 1: Handle OAuth Callback FIRST
    query_params = st.query_params
    if "code" in query_params and not st.session_state["access_token"]:
        try:
            st.info("Exchanging authorization code for token...")
            code = query_params["code"]
            st.session_state["access_token"] = fetch_access_token(code)
            st.success("Successfully logged in with Oura!")

            # Clear URL query params using JS without reloading the page
            components.html(
                """
                <script>
                    window.history.replaceState({}, document.title, window.location.pathname);
                </script>
                """,
                height=0,
            )

            st.experimental_rerun()
            return
        except Exception as e:
            st.error(f"OAuth Error: {e}")
            st.stop()

    # Step 2: Show login button if no token
    if not st.session_state["access_token"]:
        st.markdown(
            "<h3 style='text-align: center; color: white;'>Login to connect your Oura account:</h3>",
            unsafe_allow_html=True,
        )
        authorization_url = get_authorization_url()
        st.markdown(f"""
        <div style='text-align: center;'>
            <a href="{authorization_url}" target="_blank" style="
                display: inline-block;
                background-color: #1e90ff;
                color: white;
                padding: 12px 20px;
                text-decoration: none;
                border-radius: 6px;
                font-size: 18px;
            ">🔐 Login with Ōura</a>
            <p style="color: white;">After logging in, return to this tab.</p>
        </div>
        """, unsafe_allow_html=True)

        st.stop()

    # Step 3: Fetch and process data if logged in
    access_token = st.session_state["access_token"]
    try:
        data = fetch_oura_data(access_token)
        data = calculate_training_load_index(data)

        readiness_score = data["readiness_score"].iloc[-1]
        activity_score = data["activity_score"].iloc[-1]
        hrv_balance = data["hrv_balance"].iloc[-1]

        resting_hr = fetch_user_resting_hr(access_token) or 60
        max_hr = fetch_user_max_hr(access_token)

        training_load_ratio = (
            data["training_load_index"].iloc[-1]
            / data["training_load_index"].mean()
        )

        zones = adaptive_karvonen_zone_bounds(
            hr_rest=resting_hr,
            hr_max=max_hr,
            readiness=readiness_score,
            acr=training_load_ratio,
        )

        # Layout
        with st.container():
            row1_col1, row1_col2 = st.columns(2)

            with row1_col1:
                st.markdown("<h3 style='color: white;'>Training Index Over Time</h3>", unsafe_allow_html=True)
                plot_training_load_index(data)

            with row1_col2:
                st.markdown("<h3 style='color: white;'>User Metrics</h3>", unsafe_allow_html=True)
                plot_metrics(
                    readiness=readiness_score,
                    activity=activity_score,
                    resting_hr=resting_hr,
                    hrv_balance=hrv_balance,
                )

        with st.container():
            st.markdown(
                "<h3 style='text-align: center; color: white;'>Context-Driven Heart Rate Zones</h3>",
                unsafe_allow_html=True,
            )
            plot_hr_zone_ranges(zones)
            st.markdown(
                "<p style='text-align: center; color: white;'>The target heart rate zone is calculated based on your readiness score, training load ratio, and adaptive Karvonen method.</p>",
                unsafe_allow_html=True,
            )

        st.markdown(
            "<p style='text-align: center; color: white;'>Powered by Oura API</p>",
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.error(f"Failed to fetch or process data: {e}")


if __name__ == "__main__":
    main()
