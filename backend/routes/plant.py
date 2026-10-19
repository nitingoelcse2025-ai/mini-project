"""
Plant Photo Check Route for KisanMitra AI.
Accepts leaf/plant image uploads and performs disease & health diagnosis via Gemini Vision.
"""

import logging
from flask import Blueprint, request, jsonify
from services.gemini_service import generate_plant_diagnosis, GeminiRateLimitError
from database import save_query
from limiter import rate_limit_ai, sanitize_language

logger = logging.getLogger(__name__)
plant_bp = Blueprint("plant", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@plant_bp.route("/api/plant-check", methods=["POST"])
@rate_limit_ai
def plant_check():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided in request."}), 400

    file = request.files["image"]
    language = sanitize_language(request.form.get("language", "hi"))
    crop_hint = (request.form.get("crop") or "").strip()

    if len(crop_hint) > 200:
        return jsonify({"error": "Crop name cannot exceed 200 characters."}), 400

    if not file or file.filename == "":
        return jsonify({"error": "Empty filename. Please select an image."}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": "Invalid image format. Allowed formats are JPG, JPEG, PNG, and WEBP."
        }), 400

    # Read bytes and check file size
    image_bytes = file.read()
    if len(image_bytes) == 0:
        return jsonify({"error": "Uploaded image file is empty."}), 400

    if len(image_bytes) > MAX_FILE_SIZE:
        return jsonify({"error": "Image size exceeds the 5MB limit. Please upload a smaller image."}), 400

    mime_type = file.mimetype or "image/jpeg"
    if mime_type not in ["image/jpeg", "image/png", "image/webp"]:
        # Fallback based on extension
        ext = file.filename.rsplit(".", 1)[1].lower()
        mime_type = "image/png" if ext == "png" else ("image/webp" if ext == "webp" else "image/jpeg")

    try:
        diagnosis_res = generate_plant_diagnosis(
            image_bytes=image_bytes,
            mime_type=mime_type,
            language=language,
            crop=crop_hint,
        )

        if not diagnosis_res or diagnosis_res.get("source") != "ai" or not diagnosis_res.get("text"):
            # Never return a fake diagnosis if Gemini vision fails
            return jsonify({
                "error": "AI diagnosis service is currently unavailable. Please try again later. / एआई पौधा जांच सेवा वर्तमान में अनुपलब्ध है, कृपया बाद में पुनः प्रयास करें।"
            }), 503

        diagnosis_text = diagnosis_res["text"]
        source = diagnosis_res["source"]

        query_label = f"Plant Check: {file.filename}"
        if crop_hint:
            query_label += f" ({crop_hint})"

        save_query(
            query_type="plant",
            question=query_label,
            response=diagnosis_text,
            language=language,
        )

        return jsonify({
            "diagnosis": diagnosis_text,
            "language": language,
            "filename": file.filename,
            "source": source,
        }), 200

    except GeminiRateLimitError as e:
        logger.warning(f"Plant diagnosis quota exhausted: {e}")
        return jsonify({
            "error": "Gemini AI rate limit or quota exceeded. Please try again later. / एआई दर सीमा समाप्त हो गई है, कृपया बाद में पुनः प्रयास करें।"
        }), 429

    except Exception as e:
        logger.exception(f"Plant check route error: {e}")
        return jsonify({"error": "Failed to diagnose plant image. Please try again later."}), 500

