"""Gameplay Domain — Kiểm tra đáp án & tính thưởng/mốc an toàn (POST /api/game/answer)."""

import time
from flask import jsonify, request, session

from backend.core.constants import PRIZE_LEVELS, format_prize, get_safe_prize
from backend.core.security import login_required
from backend.domains.gameplay import game_bp
from backend.services.game_service import record_game_result, session_store


@game_bp.route("/api/game/answer", methods=["POST"])
@login_required
def answer_question():
    """Kiểm tra đáp án người chơi chọn, trả câu tiếp theo hoặc kết thúc ván chơi."""
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    answer = data.get("answer")

    game_sess = session_store.get_session(session_id)
    if not game_sess:
        return jsonify({"success": False, "error": "Phiên chơi không tồn tại"}), 404

    if game_sess.get("user_id") != session.get("user_id"):
        return jsonify({"success": False, "error": "Bạn không có quyền truy cập phiên chơi này"}), 403

    if not game_sess["is_active"]:
        return jsonify({"success": False, "error": "Phiên chơi đã kết thúc"}), 400

    current = game_sess["current_question"]
    question = game_sess["questions"][current]
    correct_answer = question["correct"]
    is_correct = answer == correct_answer

    if is_correct:
        game_sess["current_question"] += 1
        game_sess["prize"] = PRIZE_LEVELS[current]

        if game_sess["current_question"] >= 15:
            game_sess["is_active"] = False
            game_sess["total_time"] = int(time.time() - game_sess["start_time"])
            record_game_result(
                game_sess.get("user_id"),
                "win",
                PRIZE_LEVELS[14],
                game_sess["total_time"],
                metadata={"correct_count": 15},
            )
            return jsonify({
                "success": True,
                "is_correct": True,
                "correct_answer": correct_answer,
                "game_over": True,
                "won": True,
                "prize": format_prize(PRIZE_LEVELS[14]),
                "correct_count": 15,
                "total_time": game_sess["total_time"],
            })

        next_q = game_sess["questions"][game_sess["current_question"]].copy()
        next_q.pop("correct", None)
        return jsonify({
            "success": True,
            "is_correct": True,
            "correct_answer": correct_answer,
            "game_over": False,
            "next_question": next_q,
            "question_number": game_sess["current_question"] + 1,
            "current_prize": format_prize(game_sess["prize"]),
        })

    # Trả lời sai -> rơi về mốc an toàn
    game_sess["is_active"] = False
    game_sess["total_time"] = int(time.time() - game_sess["start_time"])
    score = get_safe_prize(current)

    record_game_result(
        game_sess.get("user_id"),
        "loss",
        score,
        game_sess["total_time"],
        metadata={"correct_count": current, "reason": "wrong_answer"},
    )
    return jsonify({
        "success": True,
        "is_correct": False,
        "correct_answer": correct_answer,
        "game_over": True,
        "won": False,
        "prize": format_prize(score),
        "correct_count": current,
        "total_time": game_sess["total_time"],
    })
