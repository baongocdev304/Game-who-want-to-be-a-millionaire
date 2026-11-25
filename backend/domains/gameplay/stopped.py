"""Gameplay Domain — Dừng cuộc chơi bảo toàn tiền thưởng (POST /api/game/stop)."""

import time
from flask import jsonify, request, session

from backend.core.constants import PRIZE_LEVELS, format_prize
from backend.core.security import login_required
from backend.domains.gameplay import game_bp
from backend.services.game_service import record_game_result, session_store


@game_bp.route("/api/game/stop", methods=["POST"])
@login_required
def stop_game():
    """Người chơi chủ động dừng cuộc chơi và bảo toàn tiền thưởng câu đã vượt qua."""
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
    prize = PRIZE_LEVELS[current - 1] if current > 0 else 0

    record_game_result(
        game_sess.get("user_id"),
        "loss",
        prize,
        game_sess["total_time"],
        metadata={"correct_count": current, "reason": "stopped"},
    )

    return jsonify({
        "success": True,
        "prize": format_prize(prize),
        "correct_count": current,
        "total_time": game_sess["total_time"],
    })
