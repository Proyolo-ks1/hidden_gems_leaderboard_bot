# helper_scripts/geo.py

import json
import time
import folium
import pandas as pd
from pathlib import Path
from geopy.geocoders import Nominatim
# Removed RateLimiter as we are manually doing time.sleep(1)

from helper_scripts.globals import LOCAL_DATA_PATH_DIR

# File path for cache
GEO_CACHE_FILE = LOCAL_DATA_PATH_DIR / "geo_cache.json"

COLOR_PALETTE = [
    '#e60049', '#0bb4ff', '#50e991', '#e6d800', '#9b19f5', 
    '#ffa300', '#dc0ab4', '#b3d4ff', '#00bfa0', '#ff0000'
]

def load_geo_cache():
    if GEO_CACHE_FILE.exists():
        try:
            return json.loads(GEO_CACHE_FILE.read_text(encoding='utf-8'))
        except:
            return {}
    return {}

def save_geo_cache(cache):
    GEO_CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding='utf-8')

def get_coordinates(city_name, cache):
    """
    Robust geocoding from Flet script, including print feedback.
    """
    clean_city = city_name.strip()
    if not clean_city:
        return None

    if clean_city in cache:
        print(f"[GEO] Cached: {clean_city}")
        return cache[clean_city]

    try:
        # Flet script logic: User Agent + Rate limiting via sleep
        geolocator = Nominatim(user_agent="hidden_gems_bot_geo")
        
        print(f"[GEO] Searching: {clean_city}...")
        
        # Try appending Germany first
        location = geolocator.geocode(f"{clean_city}, Germany")
        
        if not location:
            # Fallback to raw city name
            location = geolocator.geocode(clean_city)

        if location:
            coords = [location.latitude, location.longitude]
            cache[clean_city] = coords
            save_geo_cache(cache)
            time.sleep(1)  # Respect OpenStreetMap API limits
            print(f"[GEO] SUCCESS: {clean_city} -> {coords[0]:.2f}, {coords[1]:.2f}")
            return coords
        else:
            print(f"[GEO] FAIL: {clean_city} (Location not found)")

    except Exception as e:
        print(f"[GEO] Geocoding error for {clean_city}: {e}")

    return None

def get_city_coords_with_progress(df: pd.DataFrame):
    """
    Geocodes all unique cities in the DataFrame and prints progress to the console.
    Returns a list of dictionaries with city, coords, and count.
    """
    geo_cache = load_geo_cache()
    city_counts = df['city'].dropna().value_counts()
    cities_to_map = city_counts.index.tolist()
    max_count = city_counts.max()
    mapped_coords = []
    total_cities = len(cities_to_map)

    print(f"\n[MAPS] Starting geocoding for {total_cities} unique cities. (1 sec delay per new city)")
    
    start_time = time.time()
    
    for i, city in enumerate(cities_to_map):
        # Progress every 5 cities
        if (i + 1) % 5 == 0 or i == 0 or i == total_cities - 1:
            print(f"[MAPS] Progress: {i + 1}/{total_cities} cities processed...")
            
        coords = get_coordinates(city, geo_cache)
        
        if coords:
            mapped_coords.append({
                'city': city,
                'coords': coords,
                'count': city_counts[city]
            })

    end_time = time.time()
    print(f"[MAPS] Geocoding finished. Mapped {len(mapped_coords)} cities in {end_time - start_time:.1f} seconds.")
    
    return mapped_coords


def get_city_color(city_count, max_count):
    if max_count == 0: return COLOR_PALETTE[0]
    index = int((city_count / max_count) * (len(COLOR_PALETTE) - 1))
    return COLOR_PALETTE[index]