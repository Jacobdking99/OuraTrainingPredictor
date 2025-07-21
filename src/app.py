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


def main():
    # Set page configuration
    st.set_page_config(
        page_title="Oura Training Dashboard",
        page_icon="🌙",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Dashboard title
    st.markdown(
        "<h1 style='text-align: center; color: white;'>Oura Training Dashboard</h1>",
        unsafe_allow_html=True,
    )

    # Initialize session state variables
    if "access_token" not in st.session_state:
        st.session_state["access_token"] = None

    # Step 1: Login Button
    if not st.session_state["access_token"]:
        st.markdown(
            "<h3 style='text-align: center; color: white;'>Login to connect your Oura account:</h3>",
            unsafe_allow_html=True,
        )
        
        authorization_url = get_authorization_url()
        st.link_button("🔐 Log in with Ōura", authorization_url)

    # Step 2: Handle OAuth Callback
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        try:
            st.session_state["access_token"] = fetch_access_token(code)
            st.query_params.clear()  # Clear query params
            st.success("Successfully logged in!")
        except Exception as e:
            st.error(f"OAuth Error: {e}")
            st.stop()

    # Step 3: Fetch and Process Data
    if st.session_state["access_token"]:
        access_token = st.session_state["access_token"]
        try:
            # Fetch and process data
            data = fetch_oura_data(access_token)
            data = calculate_training_load_index(data)

            # Extract readiness, activity, and HRV balance for metrics
            readiness_score = data["readiness_score"].iloc[-1]  # Latest readiness score
            activity_score = data["activity_score"].iloc[-1]  # Latest activity score
            hrv_balance = data["hrv_balance"].iloc[-1]  # Latest HRV balance score

            # Fetch user's resting HR and max HR
            resting_hr = fetch_user_resting_hr(access_token)
            max_hr = fetch_user_max_hr(access_token)

            if resting_hr is None:
                resting_hr = 60

            # Calcualte training load ratio
            training_load_ratio = (
                data["training_load_index"].iloc[-1]
                / data["training_load_index"].mean()
            )

            # Calculate target heart rate zone
            zones = adaptive_karvonen_zone_bounds(
                hr_rest=resting_hr,
                hr_max=max_hr,
                readiness=readiness_score,
                acr=training_load_ratio,
            )

            # Layout: Two Rows
            # Row 1: Training Index Graph and User Metrics
            with st.container():
                row1_col1, row1_col2 = st.columns(2)

                with row1_col1:
                    st.markdown(
                        "<h3 style='color: white;'>Training Index Over Time</h3>",
                        unsafe_allow_html=True,
                    )
                    plot_training_load_index(data)

                with row1_col2:
                    st.markdown(
                        "<h3 style='color: white;'>User Metrics</h3>",
                        unsafe_allow_html=True,
                    )
                    plot_metrics(readiness=readiness_score, activity=activity_score, resting_hr=resting_hr, hrv_balance=hrv_balance)

            # Row 2: Target Heart Rate Zone
            with st.container():
                st.markdown(
                    "<h3 style='text-align: center; color: white;'>Context-Driven Heart Rate Zones</h3>",
                    unsafe_allow_html=True,
                )
                plot_hr_zone_ranges(zones)
                # Plot and calculation descrption
                st.markdown(
                    "<p style='text-align: center; color: white;'>The target heart rate zone is calculated based on your readiness score, training load ratio, and adaptive Karvonen method.</p>",
                    unsafe_allow_html=True,
                )
            # Footer aligned to bottom
            st.markdown(
                "<p style='text-align: center; color: white;'>Powered by Oura API</p>",
                unsafe_allow_html=True,
            )
            
                

        except Exception as e:
            st.error(f"Failed to fetch or process data: {e}")


if __name__ == "__main__":
    main()
