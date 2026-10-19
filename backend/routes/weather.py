"""
Weather Route for KisanMitra AI.
Fetches live Open-Meteo weather and provides AI-powered farming advisories.
"""

from flask import Blueprint, request, jsonify
from services.weather_service import geocode_location, fetch_weather
from services.gemini_service import generate_weather_tip
from database import save_query

weather_bp = Blueprint("weather", __name__)


@weather_bp.route("/api/weather", methods=["GET", "POST"])
def get_weather():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        city = (data.get("city") or "").strip()
        lat = data.get("lat")
        lon = data.get("lon")
        language = data.get("language", "hi")
    else:
        city = (request.args.get("city") or "").strip()
        lat = request.args.get("lat")
        lon = request.args.get("lon")
        language = request.args.get("language", "hi")

    target_lat = None
    target_lon = None
    display_name = ""

    # Case 1: Geolocation passed directly
    if lat is not None and lon is not None:
        try:
            target_lat = float(lat)
            target_lon = float(lon)
            display_name = city if city else f"Lat: {target_lat:.2f}, Lon: {target_lon:.2f}"
        except ValueError:
            return jsonify({"error": "Invalid latitude/longitude coordinates."}), 400

    # Case 2: City / village name lookup
    elif city:
        geo = geocode_location(city)
        if not geo:
            return jsonify({
                "error": f"Could not find coordinates for '{city}'. Please check the spelling or try another nearby city."
            }), 404
        target_lat, target_lon, display_name = geo

    else:
        return jsonify({"error": "Please provide a city name or GPS coordinates."}), 400

    weather_data = fetch_weather(target_lat, target_lon, display_name, lang=language)
    if not weather_data:
        return jsonify({"error": "Failed to fetch weather forecast from Open-Meteo."}), 502

    # Generate AI farming tip
    tip = generate_weather_tip(weather_data, language=language)
    weather_data["farming_tip"] = tip
    weather_data["language"] = language

    # Save to history
    save_query(
        query_type="weather",
        question=f"Weather for {display_name}",
        response=f"Temp: {weather_data['current']['temperature']}°C, Condition: {weather_data['current']['condition']}. Tip: {tip}",
        language=language,
    )

    return jsonify(weather_data), 200
