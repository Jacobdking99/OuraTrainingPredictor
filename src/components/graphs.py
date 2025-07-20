import numpy as np
import streamlit as st
import plotly.graph_objects as go


def plot_training_load_index(training_data, fit_line=True):
    """Plot the training load index over time using Plotly.
    Optionally fit linear line to show direction of change.
    """
    if fit_line:
        # Fit a linear regression line to the training load index
        x = np.arange(len(training_data["training_load_index"]))
        y = training_data["training_load_index"].values
        coefficients = np.polyfit(x, y, 1)
        trend_line = np.polyval(coefficients, x)
        training_data["trend_line"] = trend_line
    else:
        training_data["trend_line"] = None
    # Create the Plotly figure

    fig = go.Figure()


    fig.add_trace(go.Scatter(
        x=training_data["day"],
        y=training_data["training_load_index"],
        mode="lines+markers",
        line=dict(color="#1E90FF", width=3),
        marker=dict(size=8),
        name="Training Index"
    ))
    if fit_line:
        fig.add_trace(go.Scatter(
            x=training_data["day"],
            y=training_data["trend_line"],
            mode="lines",
            line=dict(color="#FF6347", width=2, dash="dash"),
            name="Trend Line"
        ))

    fig.update_layout(
        title="Training Load Index Over Time",
        xaxis_title="Date",
        yaxis_title="Training Index",
        template="plotly_dark",
        plot_bgcolor="#0E1117",
        paper_bgcolor="#0E1117",
        font=dict(color="white"),
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_metrics(readiness, activity, resting_hr, hrv_balance):
    """Display user metrics as 2×2 grid of indicators in Streamlit."""
    # First row
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        fig = go.Figure(go.Indicator(
            mode="number",
            value=readiness,
            title={"text": "Readiness"},
            number={"suffix": " / 100", "font": {"color": "#1E90FF"}},
        ))
        fig.update_layout(height=150, margin=dict(t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with row1_col2:
        fig = go.Figure(go.Indicator(
            mode="number",
            value=activity,
            title={"text": "Activity"},
            number={"suffix": " / 100", "font": {"color": "#FFD700"}},
        ))
        fig.update_layout(height=150, margin=dict(t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # Second row
    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        fig = go.Figure(go.Indicator(
            mode="number",
            value=resting_hr,
            title={"text": "Resting HR"},
            number={"suffix": " bpm", "font": {"color": "#20B2AA"}},
        ))
        fig.update_layout(height=150, margin=dict(t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with row2_col2:
        fig = go.Figure(go.Indicator(
            mode="number",
            value=hrv_balance,
            title={"text": "HRV Balance"},
            number={"suffix": " / 100", "font": {"color": "#FF4500"}},
        ))
        fig.update_layout(height=150, margin=dict(t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)


def plot_hr_zone_ranges(zones):
    """
    Plot HR zones as horizontal range bars with endpoint labels using Plotly.

    Parameters:
    - zones: dict {zone_number: (low_hr, high_hr)}
    """
    zones_sorted = sorted(zones.items())
    zone_labels = [f"Zone {z}" for z, _ in zones_sorted]
    low_values = [low for _, (low, _) in zones_sorted]
    high_values = [high for _, (_, high) in zones_sorted]
    range_widths = [high - low for low, high in zip(low_values, high_values)]

    colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336']

    fig = go.Figure()

    # Add horizontal bars
    fig.add_trace(go.Bar(
        x=range_widths,
        y=zone_labels,
        base=low_values,
        orientation='h',
        marker_color=colors[:len(zones_sorted)],
        text=[f"{low}–{high} bpm" for low, high in zip(low_values, high_values)],
        hoverinfo="text",
        marker_line=dict(color='black', width=1),
        name="HR Zones"
    ))

    # Add scatter points at start and end of each bar with text labels
    for y, low, high in zip(zone_labels, low_values, high_values):
        fig.add_trace(go.Scatter(
            x=[low, high],
            y=[y, y],
            mode="text",
            text=[f"{low}", f"{high}"],
            textposition="middle right",
            showlegend=False,
            hoverinfo="skip"
        ))

    fig.update_layout(
        title="Heart Rate Zones (Horizontal Ranges)",
        xaxis_title="Heart Rate (bpm)",
        yaxis_title="Zone",
        template="plotly_white",
        height=400,
        margin=dict(l=60, r=40, t=60, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)
