import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

CSV_FILE = "final_merged_sensor_data.csv"

# Auto-refresh every 10 seconds
st_autorefresh(interval=10000, key="datarefresh")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(CSV_FILE, parse_dates=["timestamp"])
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df = pd.DataFrame(columns=["timestamp", "temperature", "humidity"])

    df = df.drop_duplicates(subset=["timestamp"]).reset_index(drop=True)
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
    df["humidity"] = pd.to_numeric(df["humidity"], errors="coerce")
    df = df[df["timestamp"] >= pd.to_datetime("2025-08-08 12:30:28")]
    return df

st.title("Sensor Dashboard")

if st.button("Reload Data"):
    load_data.clear()
    st.success("Data reloaded!")

df = load_data()

st.subheader("Filter Options")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start date", df['timestamp'].min().date())
with col2:
    end_date = st.date_input("End date", df['timestamp'].max().date())

mask = (df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)
filtered_df = df.loc[mask]

st.subheader("Metrics to display")
show_temp = st.checkbox("Temperature (°C)", value=True)
show_hum = st.checkbox("Humidity (%)", value=True)

metrics = []
if show_temp:
    metrics.append("temperature")
if show_hum:
    metrics.append("humidity")

if not metrics:
    st.warning("Please select at least one metric!")
else:
    chart_df = filtered_df[["timestamp"] + metrics].copy()
    chart_df = chart_df.dropna(subset=["timestamp"])

    if chart_df.empty:
        st.warning("No data for the selected date range and metrics!")
    else:
        chart_type = st.selectbox("Choose visualization", ["Line Chart", "Scatter Plot", "Stacked Hourly Bar Chart"])

        color_scale = alt.Scale(domain=["temperature", "humidity"],
                                range=["#1f77b4", "#aec7e8"]) 

        if chart_type == "Line Chart":
            st.subheader("Line Chart")
            st.line_chart(chart_df.set_index("timestamp"))

        elif chart_type == "Scatter Plot":
            st.subheader("Scatter Plot")
            df_long = chart_df.melt(id_vars=["timestamp"], value_vars=metrics,
                                    var_name="metric", value_name="value")

            scatter = alt.Chart(df_long).mark_circle(size=50).encode(
                x=alt.X("timestamp:T", title="Timestamp"),
                y=alt.Y("value:Q", title="Value"),
                color=alt.Color("metric:N", scale=color_scale, title="Metric"),
                tooltip=["timestamp", "metric", "value"]
            ).interactive()

            st.altair_chart(scatter, use_container_width=True)

        elif chart_type == "Stacked Hourly Bar Chart":
            st.subheader("Stacked Hourly Bar Chart")
            df_bar = chart_df.copy()
            df_bar['hour'] = df_bar['timestamp'].dt.floor('h')
            df_long_bar = df_bar.melt(id_vars=["hour"], value_vars=metrics,
                                      var_name="metric", value_name="value")

            df_avg = df_long_bar.groupby(['hour', 'metric'], as_index=False).mean()

            stacked_chart = alt.Chart(df_avg).mark_bar().encode(
                x=alt.X("hour:T", title="Hour"),
                y=alt.Y("value:Q", title="Value"),
                color=alt.Color("metric:N", scale=color_scale, title="Metric"),
                tooltip=["hour", "metric", "value"]
            )
            st.altair_chart(stacked_chart, use_container_width=True)

if st.checkbox("Show Raw Data"):
    st.subheader("Raw Sensor Data")
    st.dataframe(filtered_df)
