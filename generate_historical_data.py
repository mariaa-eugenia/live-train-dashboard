import pandas as pd
import random

# Generate dates from January to today
date_range = pd.date_range(start="2024-01-01", end="2024-02-10")

# List of stations (same as in Streamlit dropdown)
stations = [
    "London Waterloo", "London Paddington", "London Euston", "London Victoria",
    "London Kings Cross", "London Liverpool Street", "London Bridge",
    "Manchester Piccadilly", "Birmingham New Street", "Edinburgh Waverley",
    "Glasgow Central", "Leeds", "Bristol Temple Meads", "Cardiff Central",
    "Liverpool Lime Street", "Newcastle", "Nottingham", "Sheffield",
    "Southampton Central", "Reading", "Brighton", "York", "Oxford", "Cambridge",
    "Leicester", "Norwich", "Exeter St Davids", "Plymouth"
]

# List of event days (randomly selected)
event_days = random.sample(list(date_range.strftime("%Y-%m-%d")), 10)

# Generate random delay rates for each station on each day
data = []
for date in date_range:
    for station in stations:
        delay_rate = random.randint(10, 60)  # Random delay rate between 10% and 60%
        event_day = "Yes" if date.strftime("%Y-%m-%d") in event_days else "No"
        data.append([date.strftime("%Y-%m-%d"), station, delay_rate, event_day])

# Create DataFrame
df_history = pd.DataFrame(data, columns=["Date", "Station", "Delay Rate (%)", "Event Day"])

# Save to CSV
df_history.to_csv("historical_delays.csv", index=False)

print("✅ Sample historical delay data saved as historical_delays.csv")
