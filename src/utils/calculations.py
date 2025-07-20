import pandas as pd
import streamlit as st
import requests
from datetime import datetime, timedelta


def normalize_column(col):
    """Normalize column values to a 0-1 range."""
    return (col - col.min()) / (col.max() - col.min())


def adaptive_karvonen_zone_bounds(hr_rest, hr_max, readiness, acr):
    """
    Calculate Karvonen zones adapting intensities by readiness and acute:chronic ratio (acr).

    Parameters:
    - hr_rest: resting HR
    - hr_max: max HR
    - readiness: float 0-1, higher means better recovery
    - acr: acute:chronic ratio, typical range ~0.8-1.5

    Returns:
    - dict {zone_num: (min_hr, max_hr)} with adapted zones
    """

    # Base intensities for zones
    base_intensities = {
        1: (0.50, 0.60),
        2: (0.60, 0.70),
        3: (0.70, 0.80),
        4: (0.80, 0.90),
        5: (0.90, 1.00),
    }

    hr_reserve = hr_max - hr_rest

    # Calculate modifier: 
    # readiness pushes modifier up to +10%
    # acr pushes modifier down if >1 (fatigue), or up if <1 (freshness)
    readiness_mod = 0.8 + 0.4 * readiness  # maps 0–1 to 0.8–1.2
    acr_mod = 1.1 - 0.3 * max(0, acr - 1)  # if acr >1, decrease modifier, else near 1.1 max

    # Combine them multiplicatively (tune weights as needed)
    modifier = readiness_mod * acr_mod
    # Clamp modifier between 0.85 and 1.15 to avoid extremes
    modifier = max(0.925, min(modifier, 1.075))

    zones = {}
    for zone, (low_pct, high_pct) in base_intensities.items():
        adj_low = low_pct * modifier
        adj_high = high_pct * modifier
        # Clamp adjusted intensities to max 1.0 (100%)
        adj_low = min(adj_low, 1.0)
        adj_high = min(adj_high, 1.0)

        min_hr = round(hr_rest + hr_reserve * adj_low)
        max_hr = round(hr_rest + hr_reserve * adj_high)
        zones[zone] = (min_hr, max_hr)
    return zones 


def fetch_oura_data(access_token, n_days=30):
    """Fetch activity and readiness data from the Oura API."""
    headers = {"Authorization": f"Bearer {access_token}"}

    start_date = (datetime.today() - timedelta(days=n_days)).isoformat()
    end_date = datetime.today().isoformat()

    params = {
        "start_date": start_date,
        "end_date": end_date,
    }

    # Fetch activity data
    activity_response = requests.get(
        f"https://api.ouraring.com/v2/usercollection/daily_activity", headers=headers, params=params,
    )
    activity_data = activity_response.json()["data"]
    activity_df = pd.DataFrame(activity_data)
    activity_df = pd.concat(
        [
            activity_df.drop(columns=["contributors"]),
            activity_df["contributors"].apply(pd.Series),
        ],
        axis=1,
    ).rename(columns={"score": "activity_score"})

    # Fetch readiness data
    readiness_response = requests.get(
        f"https://api.ouraring.com/v2/usercollection/daily_readiness", headers=headers, params=params,
    )
    readiness_data = readiness_response.json()["data"]
    readiness_df = pd.DataFrame(readiness_data)
    readiness_df = pd.concat(
        [
            readiness_df.drop(columns=["contributors"]),
            readiness_df["contributors"].apply(pd.Series),
        ],
        axis=1,
    ).rename(columns={"score": "readiness_score"})

    # Merge dataframes on date
    merged_df = pd.merge(
        activity_df, readiness_df, on="day", suffixes=("_activity", "_readiness")
    )

    return merged_df


def calculate_training_load_index(data):
    """Calculate the training index based on activity and readiness data."""
    
    # Calculate training load index - purely based on activity
    data["training_load_index"] = (
        normalize_column(data["activity_score"])
        + normalize_column(data["medium_activity_met_minutes"])
        + normalize_column(data["high_activity_met_minutes"])
        + normalize_column(data["training_volume"])
        + normalize_column(data["average_met_minutes"])
    )
    
    return data


def fetch_user_max_hr(access_token):
    """Fetch the user's date of birth from the Oura API and calculate their age."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        "https://api.ouraring.com/v2/usercollection/personal_info", headers=headers
    )

    if response.status_code == 200:
        user_info = response.json()
        return 220 - user_info["age"]
    else:
        st.error("Failed to fetch user info.")
        return None


def fetch_user_resting_hr(access_token, n_days=14):
    """Fetches user resting hr based ewm on resting HR from Oura API.

    Args:
        access_token (_type_): _description_
    """

    headers = {"Authorization": f"Bearer {access_token}"}
    parmas = {
        "start_datetime": (datetime.today() - timedelta(days=n_days)).isoformat(),
        "end_datetime": datetime.today().isoformat(),
    }

    response = requests.get(
        "https://api.ouraring.com/v2/usercollection/heartrate",
        headers=headers,
        params=parmas,
    )

    if response.status_code == 200:
        hr_data = response.json()["data"]
        hr_df = pd.DataFrame(hr_data)
        hr_df["day"] = pd.to_datetime(hr_df["timestamp"]).dt.date
        resting_hr_df = hr_df.loc[hr_df["source"] == "rest"]
        resting_hr_df = resting_hr_df.groupby("day").agg({"bpm": "mean"}).reset_index()
        # EWM Resting HR
        resting_hr_df["ewm_resting_hr"] = resting_hr_df["bpm"].ewm(span=14).mean()

        return resting_hr_df["ewm_resting_hr"].iloc[-1]

    else:
        st.error("Failed to fetch resting HR data.")
        return None
