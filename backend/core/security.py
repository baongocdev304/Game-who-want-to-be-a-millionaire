"""
Tầng 2A — Security & Access Control
===========================================================
File: backend/core/security.py
Mô tả: Băm/kiểm tra mật khẩu với bcrypt, decorator @login_required và
       @debug_access_required bảo vệ các route chẩn đoán.
"""

import hmac
from functools import wraps
import bcrypt
from flask import current_app, jsonify, redirect, request, session

from backend.core.extensions import get_db


def hash_password(pw: str) -> str:
    """Băm mật khẩu một chiều bằng bcrypt."""
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(pw: str, hashed: str) -> bool:
    """So khớp mật khẩu thô với chuỗi hash bcrypt."""
    return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))


def login_required(f):
    """Decorator bắt buộc đăng nhập và xác minh user_id còn tồn tại trong DB."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session or "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Vui lòng đăng nhập!"}), 401
            return redirect("/auth")

        user_id = session.get("user_id")
        conn = get_db()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
                    if not cur.fetchone():
                        session.clear()
                        if request.path.startswith("/api/"):
                            return jsonify({"success": False, "error": "Phiên đăng nhập hết hạn!"}), 401
                        return redirect("/auth")
            except Exception:
                pass
        return f(*args, **kwargs)

    return decorated


def debug_access_required(f):
    """Bảo vệ nhóm route Debug: mở khi ENABLE_DEBUG_ROUTES=True hoặc đúng X-Admin-Debug-Key."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_app.config.get("ENABLE_DEBUG_ROUTES", True):
            return f(*args, **kwargs)

        admin_key = current_app.config.get("ADMIN_DEBUG_KEY", "")
        provided_key = request.headers.get("X-Admin-Debug-Key", "")
        if admin_key and provided_key and hmac.compare_digest(provided_key, admin_key):
            return f(*args, **kwargs)

        return jsonify({
            "success": False,
            "error": "Debug routes bị khóa trên môi trường production!",
        }), 403

    return decorated
