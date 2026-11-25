"""Gameplay Domain — 3 Quyền trợ giúp: 50:50, Gọi điện, Khán giả (POST /api/game/lifeline)."""

import random
import psycopg2.extras
from flask import jsonify, request, session

from backend.core.extensions import get_db
from backend.core.security import login_required
from backend.domains.gameplay import game_bp
from backend.services.game_service import session_store
from backend.services.wallet_service import deduct_bonus_lifeline

VALID_LIFELINES = ("5050", "phone", "audience")


@game_bp.route("/api/game/lifeline", methods=["POST"])
@login_required
def use_lifeline():
    """Xử lý 3 quyền trợ giúp mặc định hoặc trừ bonus_lifelines từ ví nếu đã dùng hết trong ván."""
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    lifeline_type = data.get("type")

    if lifeline_type not in VALID_LIFELINES:
        return jsonify({"success": False, "error": "Loại trợ giúp không hợp lệ"}), 400

    game_sess = session_store.get_session(session_id)
    if not game_sess:
        return jsonify({"success": False, "error": "Phiên không tồn tại"}), 404

    if game_sess.get("user_id") != session.get("user_id"):
        return jsonify({"success": False, "error": "Bạn không có quyền truy cập phiên chơi này"}), 403

    if not game_sess["is_active"]:
        return jsonify({"success": False, "error": "Phiên chơi đã kết thúc"}), 400

    # Kiểm tra quyền mặc định còn trong ván hay phải dùng bonus_lifelines trong ví
    if not game_sess["lifelines"].get(lifeline_type, False):
        user_id = session.get("user_id")
        conn = get_db()
        if not conn:
            return jsonify({"success": False, "error": "Lỗi kết nối database!"}), 500
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                ok, err = deduct_bonus_lifeline(cur, user_id)
                if not ok:
                    conn.rollback()
                    return jsonify({"success": False, "error": err})
                conn.commit()
        except Exception as e:
            conn.rollback()
            return jsonify({"success": False, "error": f"Lỗi hệ thống ví: {str(e)}"}), 500
    else:
        game_sess["lifelines"][lifeline_type] = False

    question = game_sess["questions"][game_sess["current_question"]]
    correct = question["correct"]

    if lifeline_type == "5050":
        wrong_indices = [i for i in range(4) if i != correct]
        random.shuffle(wrong_indices)
        removed = wrong_indices[:2]
        return jsonify({
            "success": True,
            "type": "5050",
            "removed": removed,
        })

    if lifeline_type == "phone":
        if random.random() < 0.7:
            suggestion = correct
            confidence = random.randint(70, 95)
        else:
            wrong = [i for i in range(4) if i != correct]
            suggestion = random.choice(wrong)
            confidence = random.randint(30, 60)
        return jsonify({
            "success": True,
            "type": "phone",
            "suggestion": suggestion,
            "confidence": confidence,
        })

    # lifeline_type == "audience"
    percents = [0, 0, 0, 0]
    percents[correct] = random.randint(35, 70)
    remaining = 100 - percents[correct]
    for i in range(4):
        if i == correct:
            continue
        if remaining <= 0:
            percents[i] = 0
        else:
            p = random.randint(0, remaining)
            percents[i] = p
            remaining -= p
    percents[correct] += 100 - sum(percents)

    return jsonify({
        "success": True,
        "type": "audience",
        "percents": percents,
    })
