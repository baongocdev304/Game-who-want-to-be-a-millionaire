"""Domain 6: Debug (chẩn đoán nhanh hệ thống & webhook)."""

from flask import Blueprint

debug_bp = Blueprint("debug", __name__)

from backend.domains.debug import debug  # noqa: E402, F401
