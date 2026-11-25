"""Auth Domain — Đăng xuất (POST /api/auth/logout)."""

from flask import jsonify, session

from backend.domains.auth import auth_bp


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("display_name", None)
    return jsonify({"success": True})
