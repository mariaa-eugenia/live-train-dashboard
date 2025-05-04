import streamlit as st
st.set_page_config(page_title="Live Train Dashboard", page_icon="🚆", layout="wide")
import pandas as pd
import requests
import time
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
from streamlit.runtime.scriptrunner import RerunException
from streamlit.runtime.state.session_state_proxy import SessionState
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta  # ⏳ Import for API call timing

# Load API keys from .env file
load_dotenv()

#The keys are in .env file
APP_ID = os.getenv("APP_ID")
APP_KEY = os.getenv("APP_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


# ---------------------------
# 1. APP CONFIGURATION
# ---------------------------
st.title("🚆 Live UK Train Dashboard")
st.write("🔄 Auto-refreshing every 5 minutes...")

# ---------------------------
# 2. STATION DROPDOWN LIST
# ---------------------------
stations = {
    "London Waterloo": "WAT",
    "London Paddington": "PAD",
    "London Euston": "EUS",
    "London Victoria": "VIC",
    "London Kings Cross": "KGX",
    "London Liverpool Street": "LST",
    "London Bridge": "LBG",
    "Manchester Piccadilly": "MAN",
    "Birmingham New Street": "BHM",
    "Edinburgh Waverley": "EDB",
    "Glasgow Central": "GLC",
    "Leeds": "LDS",
    "Bristol Temple Meads": "BRI",
    "Cardiff Central": "CDF",
    "Liverpool Lime Street": "LIV",
    "Newcastle": "NCL",
    "Nottingham": "NOT",
    "Sheffield": "SHF",
    "Southampton Central": "SOU",
    "Reading": "RDG",
    "Brighton": "BTN",
    "York": "YRK",
    "Oxford": "OXF",
    "Cambridge": "CBG",
    "Leicester": "LEI",
    "Norwich": "NRW",
    "Exeter St Davids": "EXD",
    "Plymouth": "PLY",
}

station_name = st.selectbox("🚉 Select a Station:", list(stations.keys()))
station_code = stations[station_name]

# ---------------------------
# 3. FETCH LIVE TRAIN DATA
# ---------------------------
APP_ID = "3682f223"
APP_KEY = "9a566235e2c1bc2339d2b235e2fc7307"

# Initialize session state to store API data
if "train_data" not in st.session_state:
    st.session_state["train_data"] = None
if "last_api_call" not in st.session_state:
    st.session_state["last_api_call"] = None

def get_live_train_data(station_code):
    now = datetime.now()

    # Only call the API if the last request was more than 10 minutes ago
    if st.session_state["last_api_call"] is None or (now - st.session_state["last_api_call"]) > timedelta(minutes=10):
        url = f"https://transportapi.com/v3/uk/train/station/{station_code}/live.json"
        params = {
            "app_id": APP_ID,  # Uses .env variable
            "app_key": APP_KEY,  # Uses .env variable
            "darwin": "false",
            "train_status": "passenger"
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            if "departures" in data and "all" in data["departures"]:  # Ensure valid response
                st.session_state["train_data"] = data  # Store API response
                st.session_state["last_api_call"] = now  # Update last request time
                st.session_state["api_limit_exceeded"] = False  # Reset API limit flag
            else:
                st.warning("⚠️ API returned no train data. Keeping cached data.")

        elif "usage limits are exceeded" in response.text:
            st.warning("⚠️ API limit reached! Using last available data.")
            st.session_state["api_limit_exceeded"] = True  # Mark API as exceeded
        else:
            st.error("❌ Failed to fetch live train data. Check API credentials!")

    # Use cached data if available
    data = st.session_state.get("train_data", None)  # Avoid KeyError
    if data:
        trains = []
        for train in data.get("departures", {}).get("all", []):
            status = train["status"]

            # Make Status More User-Friendly
            if status.lower() == "on time":
                status = "✅ On Time"
            elif "delayed" in status.lower():
                status = "⚠️ Delayed"
            elif "cancelled" in status.lower():
                status = "❌ Cancelled"
            elif "arrived" in status.lower():
                status = "🚉 Arrived"
            elif "departed" in status.lower():
                status = "🚆 Departed"
            elif "starts" in status.lower():
                status = "🚦 Starts Here"

            trains.append({
                "Time": train["aimed_departure_time"],
                "Destination": train["destination_name"],
                "Status": status  # Status Formatting
            })

        if trains:  # Only process if there is data
            df = pd.DataFrame(trains)
            df["Time"] = pd.to_datetime(df["Time"], format="%H:%M", errors="coerce").dt.time  # Handle conversion errors
            df = df.sort_values(by="Time")  # 🔄 Sort by time
            return df
        else:
            return pd.DataFrame(columns=["Time", "Destination", "Status"])  # Empty but with correct columns
    
    else:
        st.warning("⚠️ No cached train data available. Please try again later.")
        return pd.DataFrame(columns=["Time", "Destination", "Status"])  # Return empty DataFrame if API fails

df = get_live_train_data(station_code)

# ---------------------------
# 4. DISPLAY TRAIN DATA
# ---------------------------
if not df.empty:
    st.subheader(f"🚆 Live Departures from {station_name} ({station_code})")
    st.dataframe(df, height=300, use_container_width=True)
else:
    st.write("❌ No live train data available.")

# ---------------------------
# 5. LOAD HISTORICAL DELAY DATA
# ---------------------------
@st.cache_data
def load_historical_data():
    return pd.read_csv("historical_delays.csv")

df_history = load_historical_data()

# Filter historical data by selected station
df_station_history = df_history[df_history["Station"] == station_name]

# Show historical data
st.subheader(f"📊 Historical Delay Data for {station_name}")
st.dataframe(df_station_history, height=300, use_container_width=True)

# ---------------------------
# 6. PLOT HISTORICAL DELAY TRENDS
# ---------------------------
fig, ax = plt.subplots(figsize=(7, 3))  # Smaller figure

# Apply moving average smoothing (3-day window)
df_station_history["Smoothed Delay Rate"] = df_station_history["Delay Rate (%)"].rolling(window=3).mean()

# Plot original delay rate in light red
ax.plot(df_station_history["Date"], df_station_history["Delay Rate (%)"], 
        marker="o", linestyle="--", color="lightcoral", alpha=0.6, label="Original")

# Plot smoothed trend in solid blue
ax.plot(df_station_history["Date"], df_station_history["Smoothed Delay Rate"], 
        marker="o", linestyle="-", color="blue", label="Smoothed")

# Formatting
ax.set_title(f"📉 Train Delay Trends for {station_name}")
ax.set_xlabel("Date")
ax.set_ylabel("Delay Rate (%)")
ax.grid(True)

# Rotate x-axis labels & reduce number of ticks
ax.set_xticks(df_station_history["Date"][::5])  # Show every 5th date
ax.set_xticklabels(df_station_history["Date"][::5], rotation=45, ha="right")

ax.legend()  # Add legend

st.pyplot(fig)

# ---------------------------
# 7. EVENT DAY VS. REGULAR DAY COMPARISON
# ---------------------------

# Extract delay rates from historical data
regular_delays = df_station_history[df_station_history["Event Day"] == "No"]["Delay Rate (%)"]
event_delays = df_station_history[df_station_history["Event Day"] == "Yes"]["Delay Rate (%)"]

# Compute average delay rates, ensuring NaN values don't break calculations
regular_delay = regular_delays.mean(skipna=True) if not regular_delays.empty else 0
event_delay = event_delays.mean(skipna=True) if not event_delays.empty else 0

# Round final values to 2 decimal places
regular_delay = round(regular_delay, 2)
event_delay = round(event_delay, 2)

# Calculate percentage difference
delay_diff = event_delay - regular_delay
delay_diff_rounded = round(delay_diff, 2)

# Delay Comparison Section
st.subheader("🎉 Delay Comparison: Event Days vs. Regular Days")

col1, col2 = st.columns(2)

with col1:
    st.markdown("🚆 **Regular Days Delay Rate**")
    st.markdown(f"<h2>{regular_delay:.2f}%</h2>", unsafe_allow_html=True)

with col2:
    st.markdown("🎊 **Event Days Delay Rate**")
    st.markdown(f"<h2>{event_delay:.2f}%</h2>", unsafe_allow_html=True)

    if abs(delay_diff) >= 0.1:  # Only show if meaningful difference
        if delay_diff > 0:
            st.markdown(f"🟢 **↑ {delay_diff_rounded}%**", unsafe_allow_html=True)
        elif delay_diff < 0:
            st.markdown(f"🔴 **↓ {abs(delay_diff_rounded)}%**", unsafe_allow_html=True)
    else:
        st.markdown("⚖️ **No significant difference**", unsafe_allow_html=True)

# Show alerts only for large differences
if delay_diff > 1:
    st.warning("⚠️ Event days have noticeably higher delay rates!")
elif delay_diff < -1:
    st.success("✅ Event days perform better than regular days!")


# ---------------------------
# 8. LIVE TRAIN MAP
# ---------------------------
train_locations = [
    {"lat": 51.5074, "lon": -0.1278, "station": "London", "status": "On Time"},
    {"lat": 53.4808, "lon": -2.2426, "station": "Manchester", "status": "Delayed"},
]

m = folium.Map(location=[53.0, -1.5], zoom_start=6)

for train in train_locations:
    color = "green" if train["status"] == "On Time" else "red"
    folium.Marker([train["lat"], train["lon"]], popup=f"{train['station']} ({train['status']})", icon=folium.Icon(color=color)).add_to(m)

st.subheader("📍 Live Train Locations")
folium_static(m)


# ---------------------------
# 9. AUTO-REFRESH EVERY 5 MINUTES
# ---------------------------
st.write("🔄 Auto-refreshing every 5 minutes...")

# Force app rerun every 5 minutes
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = time.time()

if time.time() - st.session_state["last_refresh"] > 300:  # 5 minutes
    st.session_state["last_refresh"] = time.time()
    raise RerunException(SessionState())


