"""Domain 1: Auth (register, login, logout, forgotpass)."""

from flask import Blueprint

auth_bp = Blueprint("auth", __name__)

from backend.domains.auth import register, login, logout, forgotpass  # noqa: E402, F401
