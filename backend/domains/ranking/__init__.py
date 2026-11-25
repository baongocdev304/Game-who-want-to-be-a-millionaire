"""Domain 4: Data/Ranking (history, rank)."""

from flask import Blueprint

ranking_bp = Blueprint("ranking", __name__)

from backend.domains.ranking import history, rank  # noqa: E402, F401
