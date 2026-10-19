"""
History Route for KisanMitra AI.
Manages past queries and diagnostic logs stored in SQLite.
"""

from flask import Blueprint, request, jsonify
from database import get_queries, delete_query

history_bp = Blueprint("history", __name__)


@history_bp.route("/api/history", methods=["GET"])
def list_history():
    query_type = request.args.get("type", "all").strip()
    try:
        limit = int(request.args.get("limit", 100))
    except ValueError:
        limit = 100

    try:
        records = get_queries(query_type=query_type, limit=limit)
        return jsonify({"history": records, "count": len(records)}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve history: {str(e)}"}), 500


@history_bp.route("/api/history/<int:query_id>", methods=["DELETE"])
def remove_history(query_id: int):
    try:
        deleted = delete_query(query_id)
        if not deleted:
            return jsonify({"error": f"History record with ID {query_id} not found."}), 404
        return jsonify({"message": "Record deleted successfully.", "id": query_id}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to delete history item: {str(e)}"}), 500
