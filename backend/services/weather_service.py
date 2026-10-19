"""
Weather Service for KisanMitra AI using Open-Meteo free API.
Handles:
1. Geocoding city/village names to coordinates
2. Fetching current weather and 5-day forecasts
3. Translating WMO weather codes into understandable conditions
"""

import requests
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# WMO Weather interpretation codes
WMO_DESCRIPTIONS = {
    0: {"en": "Clear sky", "hi": "साफ आसमान", "icon": "sunny"},
    1: {"en": "Mainly clear", "hi": "अधिकतर साफ", "icon": "partly-cloudy"},
    2: {"en": "Partly cloudy", "hi": "आंशिक बादल", "icon": "partly-cloudy"},
    3: {"en": "Overcast", "hi": "घने बादल", "icon": "cloudy"},
    45: {"en": "Foggy", "hi": "कोहरा", "icon": "fog"},
    48: {"en": "Depositing rime fog", "hi": "घना कोहरा", "icon": "fog"},
    51: {"en": "Light drizzle", "hi": "हल्की बूंदाबांदी", "icon": "rain"},
    53: {"en": "Moderate drizzle", "hi": "मध्यम बूंदाबांदी", "icon": "rain"},
    55: {"en": "Dense drizzle", "hi": "तेज बूंदाबांदी", "icon": "rain"},
    61: {"en": "Slight rain", "hi": "हल्की बारिश", "icon": "rain"},
    63: {"en": "Moderate rain", "hi": "मध्यम बारिश", "icon": "rain"},
    65: {"en": "Heavy rain", "hi": "भारी बारिश", "icon": "heavy-rain"},
    71: {"en": "Slight snowfall", "hi": "हल्की बर्फबारी", "icon": "snow"},
    73: {"en": "Moderate snowfall", "hi": "मध्यम बर्फबारी", "icon": "snow"},
    75: {"en": "Heavy snowfall", "hi": "भारी बर्फबारी", "icon": "snow"},
    80: {"en": "Slight rain showers", "hi": "हल्की बौछारें", "icon": "rain"},
    81: {"en": "Moderate rain showers", "hi": "मध्यम बौछारें", "icon": "rain"},
    82: {"en": "Violent rain showers", "hi": "तेज बौछारें", "icon": "heavy-rain"},
    95: {"en": "Thunderstorm", "hi": "आंधी-तूफान", "icon": "thunderstorm"},
    96: {"en": "Thunderstorm with slight hail", "hi": "ओलावृष्टि के साथ तूफान", "icon": "thunderstorm"},
    99: {"en": "Thunderstorm with heavy hail", "hi": "भारी ओलावृष्टि व तूफान", "icon": "thunderstorm"},
}


def get_weather_desc(code: int, lang: str = "en") -> Dict[str, str]:
    """Returns condition label and icon key for a WMO code."""
    entry = WMO_DESCRIPTIONS.get(code, {"en": "Clear / Mild", "hi": "साफ / सामान्य", "icon": "sunny"})
    return {
        "text": entry.get(lang if lang in ["en", "hi"] else "en", entry["en"]),
        "icon": entry["icon"],
    }


def geocode_location(location_name: str) -> Optional[Tuple[float, float, str]]:
    """
    Geocodes city or village name using Open-Meteo Geocoding API.
    Returns (latitude, longitude, formatted_display_name) or None.
    """
    clean_name = location_name.strip()
    if not clean_name:
        return None

    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": clean_name,
        "count": 1,
        "language": "en",
        "format": "json",
    }

    try:
        response = requests.get(url, params=params, timeout=8)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results")
            if results and len(results) > 0:
                first = results[0]
                lat = float(first["latitude"])
                lon = float(first["longitude"])
                name = first.get("name", clean_name)
                admin1 = first.get("admin1", "")
                country = first.get("country", "")
                parts = [p for p in [name, admin1, country] if p]
                display_name = ", ".join(parts)
                return (lat, lon, display_name)
    except Exception as e:
        logger.error(f"Geocoding error for '{clean_name}': {e}")

    return None


def fetch_weather(lat: float, lon: float, location_name: str, lang: str = "hi") -> Optional[Dict[str, Any]]:
    """
    Fetches real-time weather and 5-day daily forecast from Open-Meteo.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto",
        "forecast_days": 6,
    }

    try:
        response = requests.get(url, params=params, timeout=8)
        if response.status_code != 200:
            logger.error(f"Weather API status: {response.status_code}")
            return None

        data = response.json()
        current_raw = data.get("current", {})
        daily_raw = data.get("daily", {})

        cur_code = int(current_raw.get("weather_code", 0))
        cur_desc = get_weather_desc(cur_code, lang)

        # Current rain probability from today's daily precip prob
        daily_probs = daily_raw.get("precipitation_probability_max", [])
        current_rain_prob = daily_probs[0] if daily_probs else 0

        # Construct daily forecast for next 5 days
        forecast = []
        dates = daily_raw.get("time", [])
        max_temps = daily_raw.get("temperature_2m_max", [])
        min_temps = daily_raw.get("temperature_2m_min", [])
        daily_codes = daily_raw.get("weather_code", [])

        # Skip index 0 (today) if we want next 5 days, or include today + 4 days
        # Let's include 5 days starting from tomorrow, or 5 upcoming days
        total_days = min(len(dates), 6)
        for i in range(1, total_days):
            code = int(daily_codes[i]) if i < len(daily_codes) else 0
            desc = get_weather_desc(code, lang)
            forecast.append({
                "date": dates[i],
                "temp_max": round(max_temps[i], 1) if i < len(max_temps) else "--",
                "temp_min": round(min_temps[i], 1) if i < len(min_temps) else "--",
                "rain_probability": daily_probs[i] if i < len(daily_probs) else 0,
                "condition": desc["text"],
                "icon": desc["icon"],
                "weather_code": code,
            })

        return {
            "location_name": location_name,
            "latitude": lat,
            "longitude": lon,
            "current": {
                "temperature": round(current_raw.get("temperature_2m", 0), 1),
                "humidity": current_raw.get("relative_humidity_2m", 0),
                "wind_speed": round(current_raw.get("wind_speed_10m", 0), 1),
                "rain_probability": current_rain_prob,
                "condition": cur_desc["text"],
                "icon": cur_desc["icon"],
                "weather_code": cur_code,
            },
            "forecast": forecast[:5],
        }

    except Exception as e:
        logger.error(f"Error fetching weather for ({lat}, {lon}): {e}")
        return None
