"""Auth Domain — Quên mật khẩu & xác thực mã OTP 6 số."""

import random
from datetime import datetime, timedelta
import psycopg2.extras
from flask import jsonify, request

from backend.core.extensions import get_db
from backend.core.security import hash_password
from backend.domains.auth import auth_bp
from backend.services.mail_service import send_email_code


@auth_bp.route("/api/auth/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"success": False, "error": "Vui lòng nhập email!"})

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Lỗi database!"}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT user_id, username FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if not user:
                return jsonify({"success": False, "error": "Email này chưa được đăng ký!"})

            code = str(random.randint(100000, 999999))
            expires_at = datetime.now() + timedelta(minutes=15)

            cur.execute(
                """
                INSERT INTO password_reset_codes (user_id, code, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user["user_id"], code, expires_at),
            )
            conn.commit()

            if send_email_code(email, code):
                return jsonify({
                    "success": True,
                    "message": "Mã xác nhận đã được gửi tới email của bạn!",
                })
            return jsonify({
                "success": False,
                "error": "Không thể gửi email. Vui lòng kiểm tra lại cấu hình server.",
            })
    except Exception as e:
        conn.rollback()
        print(f"⚠️ Lỗi forgot-password: {e}")
        return jsonify({"success": False, "error": "Lỗi máy chủ nội bộ!"}), 500


@auth_bp.route("/api/auth/verify-reset-code", methods=["POST"])
def verify_reset_code():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    code = data.get("code", "").strip()
    new_password = data.get("new_password", "")

    if not email or not code or not new_password:
        return jsonify({"success": False, "error": "Vui lòng điền đầy đủ thông tin!"})
    if len(new_password) < 6:
        return jsonify({"success": False, "error": "Mật khẩu mới phải ít nhất 6 ký tự!"})

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Lỗi database!"}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if not user:
                return jsonify({"success": False, "error": "Lỗi xác minh!"})

            cur.execute(
                """
                SELECT code_id FROM password_reset_codes
                WHERE user_id = %s AND code = %s AND is_used = FALSE AND expires_at > NOW()
                ORDER BY created_at DESC LIMIT 1
                """,
                (user["user_id"], code),
            )
            if not cur.fetchone():
                return jsonify({
                    "success": False,
                    "error": "Mã xác nhận không đúng hoặc đã hết hạn!",
                })

            new_hash = hash_password(new_password)
            cur.execute(
                "UPDATE user_passwords SET password_hash = %s, last_changed = NOW() WHERE user_id = %s",
                (new_hash, user["user_id"]),
            )
            cur.execute(
                "UPDATE password_reset_codes SET is_used = TRUE WHERE user_id = %s AND code = %s",
                (user["user_id"], code),
            )

            conn.commit()
            return jsonify({"success": True, "message": "Đổi mật khẩu thành công!"})
    except Exception as e:
        conn.rollback()
        print(f"⚠️ Lỗi verify-reset-code: {e}")
        return jsonify({"success": False, "error": "Lỗi hệ thống!"}), 500
