"""
Tầng 4 — Root WSGI Entry Point
===========================================================
File: app.py
Mô tả: File cầu nối giúp Gunicorn / Docker / Render khởi chạy ứng dụng Flask
       từ thư mục gốc của repository.
"""

import os
from backend.app import app, create_app  # noqa: F401

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port)
