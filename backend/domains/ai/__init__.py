"""Domain 3: AI (chatbot, translate)."""

from flask import Blueprint

ai_bp = Blueprint("ai", __name__)

from backend.domains.ai import chatbot, translate  # noqa: E402, F401
