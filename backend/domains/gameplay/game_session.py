"""Gameplay Domain — Khởi tạo phiên chơi mới (POST /api/game/start)."""

import psycopg2.extras
from flask import jsonify, request, session

from backend.core.constants import MILESTONES, PRIZE_LEVELS, format_prize
from backend.core.extensions import get_db
from backend.core.security import login_required
from backend.domains.gameplay import game_bp
from backend.services.game_service import session_store
from backend.services.gemini_service import generate_questions_with_ai
from backend.services.question_bank import get_local_fallback_questions
from backend.services.wallet_service import deduct_game_turn


@game_bp.route("/api/game/start", methods=["POST"])
@login_required
def start_game():
    """Trừ 1 lượt chơi, chuẩn bị 15 câu hỏi (AI hoặc Offline Fallback) và mở phiên chơi mới."""
    user_id = session.get("user_id")

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Lỗi kết nối database!"}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            ok, err = deduct_game_turn(cur, user_id)
            if not ok:
                conn.rollback()
                return jsonify({"success": False, "error": err})
            conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": f"Lỗi hệ thống ví: {str(e)}"}), 500

    data = request.get_json(silent=True) or {}
    player_name = data.get("player_name") or session.get("display_name") or "Người chơi"

    # Ưu tiên sinh 15 câu hỏi qua Gemini AI; fallback sang ngân hàng offline khi có lỗi
    game_questions = generate_questions_with_ai()
    if not game_questions:
        print("ℹ️ Sử dụng bộ câu hỏi dự phòng offline...")
        game_questions = get_local_fallback_questions()

    session_id, _ = session_store.create_session(
        user_id=user_id,
        player_name=player_name,
        questions=game_questions,
    )

    first_q = game_questions[0].copy()
    first_q.pop("correct", None)

    return jsonify({
        "success": True,
        "session_id": session_id,
        "player_name": player_name,
        "question": first_q,
        "question_number": 1,
        "total_questions": 15,
        "prize_levels": [format_prize(p) for p in PRIZE_LEVELS],
        "current_prize": "0 đ",
        "milestones": list(MILESTONES.keys()),
    })
