"""AI Domain — MC Trợ Lý Ảo Gemini (POST /api/chatbot)."""

from flask import jsonify, request

from backend.domains.ai import ai_bp
from backend.services.game_service import session_store
from backend.services.gemini_service import generate_mc_reply


@ai_bp.route("/api/chatbot", methods=["POST"])
def chatbot():
    """Trò chuyện với MC Trợ Lý ảo theo ngữ cảnh phiên chơi hiện tại."""
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    session_id = data.get("session_id", "")

    game_sess = session_store.get_session(session_id) or {}
    player_name = game_sess.get("player_name", "bạn")
    current = game_sess.get("current_question", 0)

    reply = generate_mc_reply(player_name, current, message)
    return jsonify({"success": True, "reply": reply})
