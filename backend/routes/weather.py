"""
Weather Route for KisanMitra AI.
Fetches live Open-Meteo weather and provides AI-powered farming advisories.
"""

import logging
from flask import Blueprint, request, jsonify
from services.weather_service import geocode_location, fetch_weather
from services.gemini_service import generate_weather_tip, GeminiRateLimitError
from database import save_query
from limiter import rate_limit_ai, sanitize_language

logger = logging.getLogger(__name__)
weather_bp = Blueprint("weather", __name__)


@weather_bp.route("/api/weather", methods=["GET", "POST"])
@rate_limit_ai
def get_weather():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        city = (data.get("city") or "").strip()
        lat = data.get("lat")
        lon = data.get("lon")
        language = sanitize_language(data.get("language", "hi"))
        save_param = data.get("save", False) is True
    else:
        city = (request.args.get("city") or "").strip()
        lat = request.args.get("lat")
        lon = request.args.get("lon")
        language = sanitize_language(request.args.get("language", "hi"))
        save_param = str(request.args.get("save", "")).strip().lower() == "true"

    if city and len(city) > 100:
        return jsonify({"error": "City name cannot exceed 100 characters."}), 400

    target_lat = None
    target_lon = None
    display_name = ""

    # Case 1: Geolocation passed directly
    if lat is not None and lon is not None:
        try:
            target_lat = float(lat)
            target_lon = float(lon)
            display_name = city if city else f"Lat: {target_lat:.2f}, Lon: {target_lon:.2f}"
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid latitude/longitude coordinates."}), 400

    # Case 2: City / village name lookup
    elif city:
        try:
            geo = geocode_location(city)
        except Exception as e:
            logger.exception(f"Geocoding exception: {e}")
            return jsonify({"error": "Failed to look up location coordinates."}), 500

        if not geo:
            return jsonify({
                "error": f"Could not find coordinates for '{city}'. Please check the spelling or try another nearby city."
            }), 404
        target_lat, target_lon, display_name = geo

    else:
        return jsonify({"error": "Please provide a city name or GPS coordinates."}), 400

    try:
        weather_data = fetch_weather(target_lat, target_lon, display_name, lang=language)
    except Exception as e:
        logger.exception(f"Weather fetch exception: {e}")
        return jsonify({"error": "Failed to fetch weather forecast from Open-Meteo."}), 502

    if not weather_data:
        return jsonify({"error": "Failed to fetch weather forecast from Open-Meteo."}), 502

    # Generate AI farming tip
    try:
        tip_dict = generate_weather_tip(weather_data, language=language)
    except GeminiRateLimitError as e:
        logger.warning(f"Weather tip quota exhausted: {e}")
        return jsonify({
            "error": "Gemini AI rate limit or quota exceeded. Please try again later. / एआई दर सीमा समाप्त हो गई है, कृपया बाद में पुनः प्रयास करें।"
        }), 429
    except Exception as e:
        logger.exception(f"Weather tip generation exception: {e}")
        tip_dict = {
            "text": "☀️ मौसम साफ है। कृषि कार्यों के लिए सामान्य सावधानी रखें।" if language == "hi" else "☀️ Clear weather. Proceed with normal farming operations.",
            "source": "fallback",
        }

    tip_text = tip_dict.get("text", "")
    source = tip_dict.get("source", "fallback")

    weather_data["farming_tip"] = tip_text
    weather_data["source"] = source
    weather_data["language"] = language

    # Save to history ONLY when query param save=true AND live AI answer
    if save_param and source == "ai":
        save_query(
            query_type="weather",
            question=f"Weather for {display_name}",
            response=f"Temp: {weather_data['current']['temperature']}°C, Condition: {weather_data['current']['condition']}. Tip: {tip_text}",
            language=language,
        )

    return jsonify(weather_data), 200

