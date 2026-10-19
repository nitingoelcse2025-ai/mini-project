"""
History Route for KisanMitra AI.
Manages past queries and diagnostic logs stored in SQLite.
"""

import logging
from flask import Blueprint, request, jsonify
from database import get_queries, delete_query

logger = logging.getLogger(__name__)
history_bp = Blueprint("history", __name__)


@history_bp.route("/api/history", methods=["GET"])
def list_history():
    query_type = request.args.get("type", "all").strip()
    try:
        raw_limit = int(request.args.get("limit", 100))
        limit = max(1, min(raw_limit, 200))
    except (ValueError, TypeError):
        limit = 100

    try:
        records = get_queries(query_type=query_type, limit=limit)
        return jsonify({"history": records, "count": len(records)}), 200
    except Exception as e:
        logger.exception(f"History list exception: {e}")
        return jsonify({"error": "Failed to retrieve history. Please try again later."}), 500


@history_bp.route("/api/history/<int:query_id>", methods=["DELETE"])
def remove_history(query_id: int):
    try:
        deleted = delete_query(query_id)
        if not deleted:
            return jsonify({"error": f"History record with ID {query_id} not found."}), 404
        return jsonify({"message": "Record deleted successfully.", "id": query_id}), 200
    except Exception as e:
        logger.exception(f"History delete exception: {e}")
        return jsonify({"error": "Failed to delete history item. Please try again later."}), 500

