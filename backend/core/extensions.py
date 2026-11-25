"""
Tầng 2A — Core Extensions & Database Lifecycle
===========================================================
File: backend/core/extensions.py
Mô tả: Quản lý vòng đời kết nối DB theo từng HTTP request (g.db, teardown_appcontext),
       kết nối độc lập cho ghi log (standalone_db_connection) và cấu hình CORS.
"""

import sys
from contextlib import contextmanager
from flask import g
from flask_cors import CORS

from backend.config import PROJECT_ROOT

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database import create_schema, get_connection, release_connection  # noqa: E402


def get_db():
    """Lấy kết nối PostgreSQL gắn với ngữ cảnh request hiện tại (flask.g)."""
    if "db" not in g:
        g.db = get_connection()
    return g.db


def close_db(error=None):
    """Tự động trả kết nối về pool khi request kết thúc."""
    db = g.pop("db", None)
    if db is not None:
        release_connection(db)


@contextmanager
def standalone_db_connection():
    """Cấp một kết nối tách biệt khỏi g.db (dùng cho ghi webhook_logs độc lập)."""
    conn = get_connection()
    try:
        yield conn
    finally:
        if conn is not None:
            release_connection(conn)


def init_extensions(app):
    """Đăng ký CORS và vòng đời đóng kết nối DB cho Flask app."""
    CORS(app, supports_credentials=True)
    app.teardown_appcontext(close_db)


def init_db_schema(app):
    """Khởi tạo schema database an toàn khi ứng dụng khởi động."""
    try:
        with app.app_context():
            conn = get_connection()
            if conn:
                try:
                    create_schema(conn)
                    print("✅ Database schema OK!")
                finally:
                    release_connection(conn)
            else:
                print("⚠️ Không thể kết nối database khi khởi động!")
    except Exception as db_err:
        print(f"⚠️ Lỗi khởi tạo database: {db_err}")
