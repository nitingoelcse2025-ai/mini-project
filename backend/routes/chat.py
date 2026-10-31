"""
Chat Route for KisanMitra AI.
Handles multi-turn conversational agriculture queries.
"""

import logging
from flask import Blueprint, request, jsonify
from threading import Lock
import time
from services.gemini_service import generate_chat_reply, GeminiRateLimitError, check_ai_status

from database import save_query
from limiter import rate_limit_ai, sanitize_language

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)

_status_cache = {"timestamp": 0.0, "data": None}
_status_lock = Lock()


@chat_bp.route("/api/ai-status", methods=["GET"])
def ai_status():
    """
    Live AI health verification check.
    Returns JSON:
    { "key_loaded": true/false, "model": "<model name>", "live_test": "ok" | "failed", "error": "<short reason or null>" }
    Makes one tiny real Gemini call ("Say OK") to verify connection.
    NEVER logs or returns the API key. Does not save anything to the database.
    Throttled/cached for 3 seconds to avoid hammering Gemini and prevent rate limiting.
    """
    now = time.time()
    with _status_lock:
        if _status_cache["data"] is not None and (now - _status_cache["timestamp"] < 3.0):
            return jsonify(_status_cache["data"]), 200

    status_data = check_ai_status()

    with _status_lock:
        _status_cache["timestamp"] = now
        _status_cache["data"] = status_data

    return jsonify(status_data), 200


@chat_bp.route("/api/chat", methods=["POST"])
@rate_limit_ai
def chat():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages")
    language = sanitize_language(data.get("language", "hi"))

    if not messages or not isinstance(messages, list):
        return jsonify({"error": "A list of messages is required."}), 400

    if len(messages) > 20:
        return jsonify({"error": "Conversation history cannot exceed 20 messages."}), 400

    latest_user_msg = ""
    for m in reversed(messages):
        if isinstance(m, dict) and m.get("role") == "user":
            latest_user_msg = (m.get("content") or "").strip()
            break

    if not latest_user_msg:
        return jsonify({"error": "Latest message content cannot be empty."}), 400

    if len(latest_user_msg) > 1000:
        return jsonify({"error": "Message length cannot exceed 1000 characters."}), 400

    # Also validate each message length
    for m in messages:
        if isinstance(m, dict) and len(m.get("content", "")) > 1000:
            return jsonify({"error": "Individual message length cannot exceed 1000 characters."}), 400

    try:
        reply_dict = generate_chat_reply(messages, language=language)
        reply_text = reply_dict.get("text", "")
        source = reply_dict.get("source", "fallback")
        reason = reply_dict.get("reason")

        # Persist interaction into history ONLY for live AI answers
        if source == "ai":
            save_query(
                query_type="chat",
                question=latest_user_msg,
                response=reply_text,
                language=language,
            )

        resp_body = {"reply": reply_text, "language": language, "source": source}
        if reason:
            resp_body["reason"] = reason

        return jsonify(resp_body), 200

    except GeminiRateLimitError as e:
        logger.warning(f"Chat quota exhausted: {e}")
        return jsonify({
            "error": "Gemini AI rate limit or quota exceeded. Please try again later. / एआई दर सीमा समाप्त हो गई है, कृपया बाद में पुनः प्रयास करें।"
        }), 429

    except Exception as e:
        logger.exception(f"Chat route error: {e}")
        return jsonify({"error": "Failed to generate chat response. Please try again later."}), 500

