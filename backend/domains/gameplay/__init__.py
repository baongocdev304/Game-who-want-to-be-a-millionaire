"""Domain 2: Gameplay (game_session, qa, supports, stopped, endtime)."""

from flask import Blueprint

game_bp = Blueprint("gameplay", __name__)

from backend.domains.gameplay import game_session, qa, supports, stopped, endtime  # noqa: E402, F401
