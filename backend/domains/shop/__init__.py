"""Domain 5: Shop/Payment (shop, bank)."""

from flask import Blueprint

shop_bp = Blueprint("shop", __name__)

from backend.domains.shop import shop, bank  # noqa: E402, F401
