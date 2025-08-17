import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

CSV_FILE = "final_merged_sensor_data.csv"


@st.cache_data
def load_data():
    """Load and clean sensor data."""
    try:
        df = pd.read_csv(CSV_FILE, parse_dates=["timestamp"])
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df = pd.DataFrame(columns=["timestamp", "temperature", "humidity"])

    df = df.drop_duplicates(subset=["timestamp"]).reset_index(drop=True)

    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
    df["humidity"] = pd.to_numeric(df["humidity"], errors="coerce")

    df = df[df["timestamp"] >= pd.to_datetime("2025-07-01")]

    return df

if st.button("Reload Data"):
    load_data.clear()
    st.success("Data cache cleared! New data will appear after reload.")

df = load_data()

st.title("Sensor Dashboard")

st.sidebar.subheader("Filter Options")
start_date = st.sidebar.date_input("Start date", df['timestamp'].min().date())
end_date = st.sidebar.date_input("End date", df['timestamp'].max().date())
mask = (df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)
filtered_df = df.loc[mask]

st.sidebar.subheader("Metrics to display")
show_temp = st.sidebar.checkbox("Temperature", value=True)
show_hum = st.sidebar.checkbox("Humidity", value=True)

chart_type = st.selectbox("Choose chart type", ["Line Chart", "Scatter Plot", "Bar Chart"])

metrics = []
if show_temp:
    metrics.append("temperature")
if show_hum:
    metrics.append("humidity")

if not metrics:
    st.warning("Please select at least one metric to display!")
else:
    chart_df = filtered_df[["timestamp"] + metrics].copy()

    if chart_type == "Line Chart":
        st.subheader("Line Chart")
        st.line_chart(chart_df.set_index("timestamp"))

    elif chart_type == "Scatter Plot":
        st.subheader("Scatter Plot")

        df_long = chart_df.melt(id_vars=["timestamp"], value_vars=metrics,
                                var_name="metric", value_name="value")

        df_long["tooltip_value"] = df_long.apply(
            lambda row: f"{row['value']} {'C' if row['metric']=='temperature' else '%'}", axis=1
        )

        scatter_chart = alt.Chart(df_long).mark_circle(size=60).encode(
            x="timestamp:T",
            y="value:Q",
            color=alt.Color(
                "metric:N",
                scale=alt.Scale(domain=["temperature", "humidity"], range=["#0D3B66", "#76B5C5"]),
                legend=alt.Legend(title="Metric")
            ),
            tooltip=["timestamp:T", "metric:N", "tooltip_value:N"]
        ).interactive()

        st.altair_chart(scatter_chart, use_container_width=True)

    elif chart_type == "Bar Chart":
        st.subheader("Stacked Bar Chart (Hourly Average)")

        df_bar = chart_df.copy()
        df_bar['hour'] = df_bar['timestamp'].dt.floor('h')

        df_hourly = df_bar.groupby('hour')[metrics].mean().reset_index()

        df_long = df_hourly.melt(id_vars=["hour"], value_vars=metrics,
                                 var_name="metric", value_name="value")

        stacked_chart = alt.Chart(df_long).mark_bar().encode(
            x="hour:T",
            y="value:Q",
            color=alt.Color(
                "metric:N",
                scale=alt.Scale(domain=["temperature", "humidity"], range=["#0D3B66", "#76B5C5"])
            ),
            tooltip=["hour:T", "metric:N", "value:Q"]
        )
        st.altair_chart(stacked_chart, use_container_width=True)

if st.checkbox("Show Raw Data"):
    st.subheader("Raw Sensor Data")
    st.dataframe(filtered_df)
