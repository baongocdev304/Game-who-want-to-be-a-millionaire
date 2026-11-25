"""Data/Ranking Domain — Bảng xếp hạng Top 10 cao thủ (GET /api/leaderboard)."""

import psycopg2.extras
from flask import jsonify

from backend.core.extensions import get_db
from backend.domains.ranking import ranking_bp


@ranking_bp.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    """Lấy bảng xếp hạng Top 10 người chơi có tổng điểm cao nhất."""
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database error"}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                SELECT u.full_name AS player_name, r.total_score AS score, r.total_wins AS wins
                FROM rankings r
                JOIN users u ON r.user_id = u.user_id
                ORDER BY r.total_score DESC
                LIMIT 10
                """
            )
            rows = cur.fetchall()
            return jsonify({"success": True, "leaderboard": [dict(row) for row in rows]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
