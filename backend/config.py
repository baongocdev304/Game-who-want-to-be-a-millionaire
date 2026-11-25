"""
Tầng 1 — Infrastructure & Config
===========================================================
File: backend/config.py
Mô tả: Tập trung đọc, chuẩn hóa và cung cấp toàn bộ biến môi trường (.env)
       cho ứng dụng Flask, Gemini AI, SePay và SMTP Email.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def clean_env(val, default: str = "") -> str:
    """Loại bỏ comment nội dòng (ví dụ '# ghi chú') và khoảng trắng dư."""
    if not val:
        return default
    return str(val).split("#")[0].strip()


def _parse_bool(val, default: bool = False) -> bool:
    if val is None or str(val).strip() == "":
        return default
    return str(val).strip().lower() in ("1", "true", "yes", "on")


class Config:
    """Cấu hình tập trung cho toàn bộ Backend."""

    APP_VERSION = "v4-modular-4tier-2026"
    APP_ENV = clean_env(os.environ.get("APP_ENV"), "development").lower()
    DEBUG = _parse_bool(os.environ.get("FLASK_DEBUG"), default=(APP_ENV != "production"))
    PORT = int(clean_env(os.environ.get("PORT"), "5002"))

    # Flask Security
    SECRET_KEY = clean_env(os.environ.get("SECRET_KEY"), "millionaire-secret-2026-xK9mP")

    # Debug routes guard: mặc định bật ở dev, tắt ở production trừ khi bật rõ hoặc dùng Admin Key
    ENABLE_DEBUG_ROUTES = _parse_bool(
        os.environ.get("ENABLE_DEBUG_ROUTES"),
        default=(APP_ENV != "production"),
    )
    ADMIN_DEBUG_KEY = clean_env(os.environ.get("ADMIN_DEBUG_KEY"), "")

    # Google Gemini AI
    GEMINI_API_KEY = clean_env(os.environ.get("GEMINI_API_KEY"), "")
    GEMINI_MODEL = clean_env(os.environ.get("GEMINI_MODEL"), "models/gemini-flash-latest")

    # SePay & VietQR Payment
    SEPAY_BANK_CODE = clean_env(os.environ.get("SEPAY_BANK_CODE"), "MBBank")
    SEPAY_ACCOUNT_NO = clean_env(os.environ.get("SEPAY_ACCOUNT_NO"), "0123456789")
    SEPAY_ACCOUNT_NAME = clean_env(os.environ.get("SEPAY_ACCOUNT_NAME"), "AI LA TRIEU PHU")
    WEBHOOK_SECRET = clean_env(os.environ.get("WEBHOOK_SECRET"), "dev-secret-123")

    # Email SMTP (OTP Quên mật khẩu)
    MAIL_SERVER = clean_env(os.environ.get("MAIL_SERVER"), "smtp.gmail.com")
    MAIL_PORT = int(clean_env(os.environ.get("MAIL_PORT"), "587"))
    MAIL_USERNAME = clean_env(os.environ.get("MAIL_USERNAME"), "")
    MAIL_PASSWORD = clean_env(os.environ.get("MAIL_PASSWORD"), "")
    MAIL_SENDER = clean_env(
        os.environ.get("MAIL_SENDER"),
        "Ai La Trieu Phu <support@millionaire.com>",
    )
