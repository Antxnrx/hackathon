import requests
import datetime
import pandas as pd
import os
import time

# Set your TomTom API key here or in your environment variable TOMTOM_API_KEY
TOMTOM_API_KEY = os.environ.get('TOMTOM_API_KEY', 'YOUR_TOMTOM_API_KEY')

def build_tomtom_url(origin_lat, origin_lon, dest_lat, dest_lon, departure_dt):
    base_url = "https://api.tomtom.com/routing/1/calculateRoute"
    coords = f"{origin_lat},{origin_lon}:{dest_lat},{dest_lon}"
    params = {
        "key": TOMTOM_API_KEY,
        "travelMode": "car",
        "traffic": "true",
        "routeType": "fastest",
        "departureTime": departure_dt.isoformat(),  # e.g., 2025-04-10T08:30:00
        "computeTravelTimeFor": "all"
    }
    return f"{base_url}/{coords}/json", params

def get_live_travel_time(origin_lat, origin_lon, dest_lat, dest_lon, departure_dt):
    url, params = build_tomtom_url(origin_lat, origin_lon, dest_lat, dest_lon, departure_dt)
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        travel_time_sec = data['routes'][0]['summary']['travelTimeInSeconds']
        return travel_time_sec / 60.0  # convert seconds to minutes
    except Exception as e:
        print(f"Error fetching from TomTom: {e}")
        return None

def bulk_fetch_travel_times(df):
    results = []
    for idx, row in df.iterrows():
        if row['Trip_Type'] == 'morning':
            origin_lat, origin_lon = row['Home_Lat'], row['Home_Lon']
            dest_lat, dest_lon = row['Office_Lat'], row['Office_Lon']
        else:
            origin_lat, origin_lon = row['Office_Lat'], row['Office_Lon']
            dest_lat, dest_lon = row['Home_Lat'], row['Home_Lon']

        # Convert Time_Of_Day (e.g., 830) to hours and minutes and combine with Date
        hour = int(row['Time_Of_Day'] // 100)
        minute = int(row['Time_Of_Day'] % 100)
        # Make sure Date is parsed as a date object; if read from CSV, use parse_dates
        departure_dt = datetime.datetime(row['Date'].year, row['Date'].month, row['Date'].day, hour, minute)
        
        travel_time = get_live_travel_time(origin_lat, origin_lon, dest_lat, dest_lon, departure_dt)
        results.append(travel_time)
        time.sleep(0.5)  # avoid hitting API too fast
    df['Live_Travel_Time'] = results
    return df

if __name__ == "__main__":
    synthetic_data = pd.read_csv("../data/synthetic_data.csv", parse_dates=["Date"])
    updated_data = bulk_fetch_travel_times(synthetic_data)
    updated_data.to_csv("../data/traffic_cache.csv", index=False)
    print("Live traffic times fetched and saved to ../data/traffic_cache.csv")
