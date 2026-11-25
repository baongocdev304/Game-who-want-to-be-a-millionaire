"""
Tầng 3 — Domain Blueprints Registry
===========================================================
File: backend/domains/__init__.py
Mô tả: Đăng ký toàn bộ 6 nhóm Domain Blueprints độc lập vào Flask app.
"""

from backend.domains.auth import auth_bp
from backend.domains.gameplay import game_bp
from backend.domains.ai import ai_bp
from backend.domains.ranking import ranking_bp
from backend.domains.shop import shop_bp
from backend.domains.debug import debug_bp


def register_blueprints(app):
    """Đăng ký 6 nhóm domain controllers theo đúng Separation of Concerns."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(ranking_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(debug_bp)
