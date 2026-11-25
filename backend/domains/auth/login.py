"""Auth Domain — Đăng nhập, kiểm tra phiên và render trang chính/auth."""

import psycopg2.extras
from flask import jsonify, redirect, render_template, request, session

from backend.core.extensions import get_db
from backend.core.security import check_password, login_required
from backend.domains.auth import auth_bp


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Lỗi kết nối database!"}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                SELECT u.user_id, u.username, u.full_name, p.password_hash
                FROM users u
                JOIN user_passwords p ON u.user_id = p.user_id
                WHERE u.username = %s
                """,
                (username,),
            )
            user = cur.fetchone()

            if not user:
                return jsonify({"success": False, "error": "Tên đăng nhập không tồn tại!"})

            if not check_password(password, user["password_hash"]):
                return jsonify({"success": False, "error": "Mật khẩu không đúng!"})

            session["username"] = user["username"]
            session["user_id"] = user["user_id"]
            session["display_name"] = user["full_name"]
            return jsonify({"success": True, "display_name": user["full_name"]})
    except Exception as e:
        return jsonify({"success": False, "error": f"Lỗi hệ thống: {str(e)}"}), 500


@auth_bp.route("/api/auth/me", methods=["GET"])
def me():
    if "username" in session:
        return jsonify({
            "logged_in": True,
            "username": session["username"],
            "display_name": session.get("display_name", session["username"]),
        })
    return jsonify({"logged_in": False})


@auth_bp.route("/")
@login_required
def index():
    """Trang chơi game chính (chỉ vào được khi đã đăng nhập)."""
    return render_template("index.html")


@auth_bp.route("/auth")
def auth_page():
    """Trang đăng nhập / đăng ký / quên mật khẩu."""
    if "username" in session:
        return redirect("/")
    return render_template("signin.html")
