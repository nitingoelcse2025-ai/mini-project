"""
Chat Route for KisanMitra AI.
Handles multi-turn conversational agriculture queries.
"""

from flask import Blueprint, request, jsonify
from services.gemini_service import generate_chat_reply
from database import save_query

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages")
    language = data.get("language", "hi")

    if not messages or not isinstance(messages, list):
        return jsonify({"error": "A list of messages is required."}), 400

    latest_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            latest_user_msg = m.get("content", "").strip()
            break

    if not latest_user_msg:
        return jsonify({"error": "Latest message content cannot be empty."}), 400

    try:
        reply = generate_chat_reply(messages, language=language)
        # Persist interaction into history
        save_query(
            query_type="chat",
            question=latest_user_msg,
            response=reply,
            language=language,
        )
        return jsonify({"reply": reply, "language": language}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to generate response: {str(e)}"}), 500
