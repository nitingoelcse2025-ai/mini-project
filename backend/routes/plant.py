"""
Plant Photo Check Route for KisanMitra AI.
Accepts leaf/plant image uploads and performs disease & health diagnosis via Gemini Vision.
"""

from flask import Blueprint, request, jsonify
from services.gemini_service import generate_plant_diagnosis
from database import save_query

plant_bp = Blueprint("plant", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@plant_bp.route("/api/plant-check", methods=["POST"])
def plant_check():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided in request."}), 400

    file = request.files["image"]
    language = request.form.get("language", "hi")
    crop_hint = request.form.get("crop", "").strip()

    if file.filename == "":
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
        diagnosis = generate_plant_diagnosis(
            image_bytes=image_bytes,
            mime_type=mime_type,
            language=language,
        )

        query_label = f"Plant Check: {file.filename}"
        if crop_hint:
            query_label += f" ({crop_hint})"

        save_query(
            query_type="plant",
            question=query_label,
            response=diagnosis,
            language=language,
        )

        return jsonify({
            "diagnosis": diagnosis,
            "language": language,
            "filename": file.filename,
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to diagnose plant image: {str(e)}"}), 500
