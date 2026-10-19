"""
Chat Route for KisanMitra AI.
Handles multi-turn conversational agriculture queries.
"""

import logging
from flask import Blueprint, request, jsonify
from services.gemini_service import generate_chat_reply, GeminiRateLimitError
from database import save_query
from limiter import rate_limit_ai, sanitize_language

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)


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

        # Persist interaction into history ONLY for live AI answers
        if source == "ai":
            save_query(
                query_type="chat",
                question=latest_user_msg,
                response=reply_text,
                language=language,
            )

        return jsonify({"reply": reply_text, "language": language, "source": source}), 200

    except GeminiRateLimitError as e:
        logger.warning(f"Chat quota exhausted: {e}")
        return jsonify({
            "error": "Gemini AI rate limit or quota exceeded. Please try again later. / एआई दर सीमा समाप्त हो गई है, कृपया बाद में पुनः प्रयास करें।"
        }), 429

    except Exception as e:
        logger.exception(f"Chat route error: {e}")
        return jsonify({"error": "Failed to generate chat response. Please try again later."}), 500

