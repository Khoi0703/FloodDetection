import pickle
import os
import time
from dagster import asset
import pandas as pd
from utils.geojson_utils import load_geojson, get_province_coordinates
from utils.weather_utils import get_weather_forecast

CACHE_FILE = "weather_cache.pkl"
CACHE_EXPIRY = 3600  # 1 giờ

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            cache = pickle.load(f)
            if time.time() - cache["timestamp"] < CACHE_EXPIRY:
                return cache["data"]
    return {}

def save_cache(data):
    with open(CACHE_FILE, "wb") as f:
        pickle.dump({"timestamp": time.time(), "data": data}, f)

@asset
def vietnam_geojson():
    return load_geojson()

@asset
def province_coordinates(vietnam_geojson):
    coordinates = {}
    for feature in vietnam_geojson["features"]:
        province = feature["properties"]["ten_tinh"]
        lat, lon = get_province_coordinates(province, vietnam_geojson)
        if lat and lon:
            coordinates[province] = {"lat": lat, "lon": lon}
    return coordinates

@asset
def weather_forecasts(province_coordinates):
    # Load cache
    forecasts = load_cache()

    for province, coords in province_coordinates.items():
        if province not in forecasts:
            forecast, total_rain = get_weather_forecast(coords["lat"], coords["lon"])
            if forecast:
                forecasts[province] = {
                    "forecast": pd.DataFrame(forecast),
                    "total_rain": total_rain
                }

    # Save updated cache
    save_cache(forecasts)
    return forecasts
