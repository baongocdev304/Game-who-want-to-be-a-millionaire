"""
Tầng 4 — Application Bootstrap & Factory
===========================================================
File: backend/app.py
Mô tả: Application Factory create_app() khởi tạo Flask app, nạp Config,
       gắn Extensions (CORS & vòng đời DB), khởi tạo Schema, đăng ký
       6 nhóm Domain Blueprints và các route tĩnh PWA.

Hỗ trợ chạy linh hoạt cả 2 cách:
  - Từ root:     python app.py   hoặc  gunicorn app:app
  - Từ backend/: cd backend && python app.py  hoặc  gunicorn app:app
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, send_from_directory  # noqa: E402

from backend.config import Config  # noqa: E402
from backend.core.extensions import init_db_schema, init_extensions  # noqa: E402
from backend.domains import register_blueprints  # noqa: E402


def create_app(config_override: dict | None = None, init_db: bool = True) -> Flask:
    """Application Factory tạo và cấu hình toàn bộ ứng dụng Flask."""
    static_dir = str(PROJECT_ROOT / "static")
    template_dir = str(PROJECT_ROOT / "templates")

    flask_app = Flask(
        __name__,
        static_folder=static_dir,
        template_folder=template_dir,
    )

    flask_app.config.from_object(Config)
    if config_override:
        flask_app.config.update(config_override)
    flask_app.secret_key = flask_app.config["SECRET_KEY"]

    # Tầng 2: CORS & vòng đời kết nối Database per-request
    init_extensions(flask_app)

    # Tầng 3: Đăng ký 6 nhóm Domain Blueprints độc lập
    register_blueprints(flask_app)

    # PWA Routes (Tầng 4)
    @flask_app.route("/manifest.json")
    def manifest():
        return send_from_directory(static_dir, "manifest.json")

    @flask_app.route("/sw.js")
    def service_worker():
        return send_from_directory(static_dir, "sw.js")

    # Tầng 1: Kiểm tra & khởi tạo Schema Database khi khởi động
    if init_db:
        init_db_schema(flask_app)

    return flask_app


# WSGI app instance mặc định (dùng bởi Gunicorn / Render / Root app.py)
app = create_app()


if __name__ == "__main__":
    print("=" * 52)
    print("AI LA TRIEU PHU - SERVER (4-Tier Modular Backend)")
    print("=" * 52)
    print(f" Web: http://localhost:{Config.PORT}")
    print("=" * 52)
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
