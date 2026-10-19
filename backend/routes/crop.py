"""
Crop Advice Route for KisanMitra AI.
Provides sowing, irrigation, care, pests, and fertilizer recommendations.
"""

from flask import Blueprint, request, jsonify
from services.gemini_service import generate_crop_advice
from database import save_query

crop_bp = Blueprint("crop", __name__)


@crop_bp.route("/api/crop-advice", methods=["POST"])
def crop_advice():
    data = request.get_json(silent=True) or {}
    crop = (data.get("crop") or "").strip()
    season = (data.get("season") or "").strip()
    soil = (data.get("soil") or "").strip()
    question = (data.get("question") or "").strip()
    language = data.get("language", "hi")

    if not crop:
        return jsonify({"error": "Crop name is required."}), 400
    if not season:
        return jsonify({"error": "Season is required (e.g. Kharif, Rabi, Zaid)."}), 400

    try:
        advice = generate_crop_advice(
            crop=crop,
            season=season,
            soil=soil,
            question=question,
            language=language,
        )

        query_summary = f"{crop} ({season})"
        if soil:
            query_summary += f", Soil: {soil}"
        if question:
            query_summary += f" - {question}"

        save_query(
            query_type="crop",
            question=query_summary,
            response=advice,
            language=language,
        )

        return jsonify({
            "crop": crop,
            "season": season,
            "advice": advice,
            "language": language,
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to generate crop advice: {str(e)}"}), 500
