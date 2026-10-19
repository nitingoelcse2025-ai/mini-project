"""
Crop Advice Route for KisanMitra AI.
Provides sowing, irrigation, care, pests, and fertilizer recommendations.
"""

import logging
from flask import Blueprint, request, jsonify
from services.gemini_service import generate_crop_advice, GeminiRateLimitError
from database import save_query
from limiter import rate_limit_ai, sanitize_language

logger = logging.getLogger(__name__)
crop_bp = Blueprint("crop", __name__)


@crop_bp.route("/api/crop-advice", methods=["POST"])
@rate_limit_ai
def crop_advice():
    data = request.get_json(silent=True) or {}
    crop = (data.get("crop") or "").strip()
    season = (data.get("season") or "").strip()
    soil = (data.get("soil") or "").strip()
    question = (data.get("question") or "").strip()
    language = sanitize_language(data.get("language", "hi"))

    if not crop:
        return jsonify({"error": "Crop name is required."}), 400
    if len(crop) > 200:
        return jsonify({"error": "Crop name cannot exceed 200 characters."}), 400

    if not season:
        return jsonify({"error": "Season is required (e.g. Kharif, Rabi, Zaid)."}), 400
    if len(season) > 50:
        return jsonify({"error": "Season cannot exceed 50 characters."}), 400

    if len(soil) > 100:
        return jsonify({"error": "Soil type cannot exceed 100 characters."}), 400

    if len(question) > 500:
        return jsonify({"error": "Question cannot exceed 500 characters."}), 400

    try:
        advice_dict = generate_crop_advice(
            crop=crop,
            season=season,
            soil=soil,
            question=question,
            language=language,
        )
        advice_text = advice_dict.get("text", "")
        source = advice_dict.get("source", "fallback")

        # Persist interaction into history ONLY for live AI answers
        if source == "ai":
            query_summary = f"{crop} ({season})"
            if soil:
                query_summary += f", Soil: {soil}"
            if question:
                query_summary += f" - {question}"

            save_query(
                query_type="crop",
                question=query_summary,
                response=advice_text,
                language=language,
            )

        return jsonify({
            "crop": crop,
            "season": season,
            "advice": advice_text,
            "language": language,
            "source": source,
        }), 200

    except GeminiRateLimitError as e:
        logger.warning(f"Crop advice quota exhausted: {e}")
        return jsonify({
            "error": "Gemini AI rate limit or quota exceeded. Please try again later. / एआई दर सीमा समाप्त हो गई है, कृपया बाद में पुनः प्रयास करें।"
        }), 429

    except Exception as e:
        logger.exception(f"Crop route error: {e}")
        return jsonify({"error": "Failed to generate crop advice. Please try again later."}), 500

