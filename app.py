import streamlit as st
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

# The keys are in .env file
APP_ID = os.getenv("APP_ID")
APP_KEY = os.getenv("APP_KEY")

# ---------------------------
# 🚆 1. APP CONFIGURATION
# ---------------------------
st.set_page_config(page_title="Live Train Dashboard", page_icon="🚆", layout="wide")

st.title("🚆 Live UK Train Dashboard")
st.write("🔄 Auto-refreshing every 5 minutes...")

# ---------------------------
# 🚉 2. STATION DROPDOWN LIST
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
# 🔄 3. FETCH LIVE TRAIN DATA (WITH CACHING)
# ---------------------------

# ✅ Initialize session state to store API data
if "train_data" not in st.session_state or "last_api_call" not in st.session_state:
    st.session_state["train_data"] = None
    st.session_state["last_api_call"] = None

def get_live_train_data(station_code):
    now = datetime.now()

    # ✅ Only call the API if last request was more than 5 minutes ago
    if st.session_state["last_api_call"] is None or (now - st.session_state["last_api_call"]) > timedelta(minutes=5):
        url = f"https://transportapi.com/v3/uk/train/station/{station_code}/live.json"
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "darwin": "false",
            "train_status": "passenger"
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            st.session_state["train_data"] = data  # Store API response
            st.session_state["last_api_call"] = now  # Update last request time
        else:
            st.warning("⚠️ Could not fetch train data. Using cached data.")

    return st.session_state["train_data"]

# Fetch train data (cached version)
data = get_live_train_data(station_code)

# ✅ Process and format the train data for display
if data:
    trains = []
    for train in data["departures"]["all"]:
        status = train["status"]

        # 🚀 Make Status More User-Friendly
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
            "Status": status  # ✅ Status Formatting
        })

    if trains:
        df = pd.DataFrame(trains)
        df["Time"] = pd.to_datetime(df["Time"], format="%H:%M", errors="coerce").dt.time  # Convert Time to datetime
        df = df.sort_values(by="Time")  # 🔄 Sort by time
    else:
        df = pd.DataFrame(columns=["Time", "Destination", "Status"])
else:
    df = pd.DataFrame(columns=["Time", "Destination", "Status"])  # Empty DataFrame if API fails

# ---------------------------
# 📊 4. DISPLAY TRAIN DATA
# ---------------------------
if not df.empty:
    st.subheader(f"🚆 Live Departures from {station_name} ({station_code})")
    st.dataframe(df, height=300, use_container_width=True)
else:
    st.write("❌ No live train data available.")

# ---------------------------
# 🔄 5. AUTO-REFRESH EVERY 5 MINUTES
# ---------------------------
st.write("🔄 Auto-refreshing every 5 minutes...")

if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = time.time()

if time.time() - st.session_state["last_refresh"] > 300:  # 5 minutes
    st.session_state["last_refresh"] = time.time()
    raise RerunException(SessionState())



