"""
Tầng 2B — Email SMTP Service
===========================================================
File: backend/services/mail_service.py
Mô tả: Gửi mã xác nhận OTP 6 số qua SMTP (smtplib + TLS).
       Nếu chưa cấu hình MAIL_USERNAME/MAIL_PASSWORD, tự động in console để hỗ trợ dev.
"""

import smtplib
from email.header import Header
from email.mime.text import MIMEText

from backend.config import Config


def send_email_code(receiver_email: str, code: str) -> bool:
    """Gửi mã OTP khôi phục mật khẩu 6 số tới receiver_email."""
    print(f"\n[EMAIL] Gửi tới {receiver_email}: Mã xác nhận = {code}\n")

    if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
        return True

    try:
        subject = "Mã xác nhận khôi phục mật khẩu - Ai Là Triệu Phú"
        body = (
            f"Chào bạn,\n\n"
            f"Mã xác nhận của bạn để đặt lại mật khẩu là: {code}\n\n"
            f"Mã này sẽ hết hạn sau 15 phút. Nếu không phải bạn yêu cầu, vui lòng bỏ qua email này."
        )
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = Config.MAIL_SENDER
        msg["To"] = receiver_email

        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
            server.starttls()
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.sendmail(Config.MAIL_USERNAME, receiver_email, msg.as_string())
        return True
    except Exception as e:
        print(f"⚠️ Lỗi gửi email: {e}")
        return False
