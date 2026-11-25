"""Gameplay Domain — Xử lý hết 30 giây suy nghĩ (POST /api/game/timeout)."""

import time
from flask import jsonify, request, session

from backend.core.constants import format_prize, get_safe_prize
from backend.core.security import login_required
from backend.domains.gameplay import game_bp
from backend.services.game_service import record_game_result, session_store


@game_bp.route("/api/game/timeout", methods=["POST"])
@login_required
def timeout():
    """Kết thúc ván chơi khi hết thời gian, nhận tiền thưởng theo mốc an toàn."""
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")

    game_sess = session_store.get_session(session_id)
    if not game_sess:
        return jsonify({"success": False, "error": "Phiên không tồn tại"}), 404

    if game_sess.get("user_id") != session.get("user_id"):
        return jsonify({"success": False, "error": "Bạn không có quyền truy cập phiên chơi này"}), 403

    if not game_sess["is_active"]:
        return jsonify({"success": False, "error": "Phiên chơi đã kết thúc"}), 400

    game_sess["is_active"] = False
    game_sess["total_time"] = int(time.time() - game_sess["start_time"])

    current = game_sess["current_question"]
    correct = game_sess["questions"][current]["correct"]
    score = get_safe_prize(current)

    record_game_result(
        game_sess.get("user_id"),
        "loss",
        score,
        game_sess["total_time"],
        metadata={"correct_count": current, "reason": "timeout"},
    )

    return jsonify({
        "success": True,
        "correct_answer": correct,
        "prize": format_prize(score),
        "correct_count": current,
        "total_time": game_sess["total_time"],
    })
