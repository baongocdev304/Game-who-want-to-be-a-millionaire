"""AI Domain — Dịch câu hỏi hiện tại bằng Gemini AI (POST /api/translate)."""

from flask import jsonify, request

from backend.domains.ai import ai_bp
from backend.services.game_service import session_store
from backend.services.gemini_service import get_gemini_client, translate_question_with_ai


@ai_bp.route("/api/translate", methods=["POST"])
def translate_question():
    """Dịch câu hỏi và 4 phương án trả lời sang ngôn ngữ đích."""
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    target_lang = data.get("target_lang", "Tiếng Anh")

    game_sess = session_store.get_session(session_id)
    if not game_sess:
        return jsonify({"success": False, "error": "Phiên chơi không tồn tại"}), 404

    if not get_gemini_client():
        return jsonify({"success": False, "error": "Chưa cấu hình GEMINI_API_KEY"}), 500

    current = game_sess["current_question"]
    question = game_sess["questions"][current]

    try:
        translated_data = translate_question_with_ai(
            question["question"],
            question["answers"],
            target_lang,
        )
        return jsonify({"success": True, "translated": translated_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
