"""Shop/Payment Domain — Ví người dùng, tạo đơn VietQR, polling & lịch sử nạp."""

import time
import urllib.parse
import uuid
import psycopg2.extras
from flask import current_app, jsonify, request, session

from backend.config import Config
from backend.core.constants import SHOP_PRICES
from backend.core.extensions import get_db
from backend.core.security import login_required
from backend.domains.shop import shop_bp
from backend.services.wallet_service import get_or_create_wallet


@shop_bp.route("/api/shop/wallet", methods=["GET"])
@login_required
def get_shop_wallet():
    """Lấy số dư lượt chơi và lượt trợ giúp dự phòng hiện tại của user."""
    user_id = session.get("user_id")
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Lỗi kết nối database!"}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            wallet = get_or_create_wallet(cur, user_id)
            conn.commit()
            return jsonify({
                "success": True,
                "game_turns": wallet["game_turns"],
                "bonus_lifelines": wallet["bonus_lifelines"],
            })
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@shop_bp.route("/api/shop/create-order", methods=["POST"])
@login_required
def create_shop_order():
    """Tạo đơn hàng trạng thái pending và sinh mã QR VietQR cho SePay."""
    data = request.get_json(silent=True) or {}
    item_type = data.get("item_type")
    quantity = data.get("quantity")

    if (
        item_type not in SHOP_PRICES
        or isinstance(quantity, bool)
        or not isinstance(quantity, int)
        or quantity <= 0
    ):
        return jsonify({"success": False, "error": "Dữ liệu không hợp lệ!"}), 400

    total_price = SHOP_PRICES[item_type] * quantity
    user_id = session.get("user_id")
    payment_ref = f"AMT_{int(time.time())}_{uuid.uuid4().hex[:6].upper()}"

    bank_code = current_app.config.get("SEPAY_BANK_CODE", Config.SEPAY_BANK_CODE)
    account_no = current_app.config.get("SEPAY_ACCOUNT_NO", Config.SEPAY_ACCOUNT_NO)
    account_name = current_app.config.get("SEPAY_ACCOUNT_NAME", Config.SEPAY_ACCOUNT_NAME)

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Lỗi kết nối database!"}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                INSERT INTO shop_transactions (user_id, item_type, quantity, total_price, payment_ref, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
                """,
                (user_id, item_type, quantity, total_price, payment_ref),
            )
            conn.commit()

        qr_url = (
            f"https://img.vietqr.io/image/{bank_code}-{account_no}-compact2.png"
            f"?amount={total_price}&addInfo={urllib.parse.quote(payment_ref)}"
            f"&accountName={urllib.parse.quote(account_name)}"
        )
        return jsonify({
            "success": True,
            "txn_id": payment_ref,
            "payment_ref": payment_ref,
            "total_price": total_price,
            "qr_url": qr_url,
            "bank_code": bank_code,
            "account_no": account_no,
            "account_name": account_name,
        })
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@shop_bp.route("/api/shop/check-status", methods=["GET"])
@login_required
def check_order_status():
    """Kiểm tra trạng thái đơn hàng theo payment_ref (Frontend polling)."""
    payment_ref = request.args.get("ref")
    if not payment_ref:
        return jsonify({"success": False, "error": "Thiếu payment_ref"}), 400

    user_id = session.get("user_id")
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Lỗi kết nối database!"}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "SELECT status FROM shop_transactions WHERE payment_ref = %s AND user_id = %s",
                (payment_ref, user_id),
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"success": False, "error": "Không tìm thấy giao dịch"}), 404
            return jsonify({"success": True, "status": row["status"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@shop_bp.route("/api/shop/history", methods=["GET"])
@login_required
def get_shop_history():
    """Lấy danh sách 20 giao dịch nạp gần nhất của người dùng."""
    user_id = session.get("user_id")
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Lỗi kết nối database!"}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                SELECT item_type, quantity, total_price, payment_ref, status, created_at
                FROM shop_transactions
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (user_id,),
            )
            rows = cur.fetchall()
            txns = []
            for r in rows:
                txn = dict(r)
                if txn.get("created_at"):
                    txn["created_at"] = txn["created_at"].isoformat()
                txns.append(txn)
            return jsonify({"success": True, "transactions": txns})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
