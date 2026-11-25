"""Debug Domain — Các route chẩn đoán hệ thống, regex, webhook logs & giao dịch."""

import psycopg2.extras
from flask import current_app, jsonify

from backend.config import Config
from backend.core.constants import AMT_REF_PATTERN
from backend.core.extensions import get_db
from backend.core.security import debug_access_required
from backend.domains.debug import debug_bp


@debug_bp.route("/api/debug/status", methods=["GET"])
@debug_access_required
def debug_status():
    """Kiểm tra phiên bản kiến trúc, kết nối DB, regex và 5 giao dịch gần nhất."""
    result = {
        "version": current_app.config.get("APP_VERSION", Config.APP_VERSION),
        "db_connected": False,
        "tables_exist": False,
        "regex_test": None,
        "recent_transactions": [],
    }

    conn = get_db()
    if conn:
        result["db_connected"] = True
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT COUNT(*) FROM shop_transactions")
                result["tables_exist"] = True

                cur.execute(
                    """
                    SELECT payment_ref, status, item_type, quantity, total_price, created_at
                    FROM shop_transactions
                    ORDER BY created_at DESC LIMIT 5
                    """
                )
                for row in cur.fetchall():
                    result["recent_transactions"].append({
                        "ref": row["payment_ref"],
                        "status": row["status"],
                        "item": row["item_type"],
                        "qty": row["quantity"],
                        "price": row["total_price"],
                        "created": str(row["created_at"]),
                    })
        except Exception as e:
            result["db_error"] = str(e)

    test_content = "NHAN TU 06300420066666 TRACE 440721 ND AMT1780089184466B9A"
    match = AMT_REF_PATTERN.search(test_content)
    if match:
        result["regex_test"] = {
            "input": test_content,
            "matched": True,
            "payment_ref": f"AMT_{match.group(1)}_{match.group(2).upper()}",
        }
    else:
        result["regex_test"] = {"input": test_content, "matched": False}

    return jsonify(result)


@debug_bp.route("/api/debug/webhooks", methods=["GET"])
@debug_access_required
def debug_webhooks():
    """Hiển thị 20 bản ghi nhật ký webhook gần nhất."""
    result = {"db_connected": False, "logs": []}
    conn = get_db()
    if conn:
        result["db_connected"] = True
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(
                    """
                    SELECT log_id, received_at, ip_address, headers, payload,
                           is_authenticated, auth_step, payment_ref, matched, error_message, status_code
                    FROM webhook_logs
                    ORDER BY received_at DESC LIMIT 20
                    """
                )
                for row in cur.fetchall():
                    result["logs"].append({
                        "id": row["log_id"],
                        "time": str(row["received_at"]),
                        "ip": row["ip_address"],
                        "headers": row["headers"],
                        "payload": row["payload"],
                        "auth": row["is_authenticated"],
                        "auth_step": row["auth_step"],
                        "ref": row["payment_ref"],
                        "matched": row["matched"],
                        "error": row["error_message"],
                        "status": row["status_code"],
                    })
        except Exception as e:
            result["db_error"] = str(e)

    return jsonify(result)


@debug_bp.route("/api/debug/transaction/<ref>", methods=["GET"])
@debug_access_required
def debug_transaction(ref):
    """Tra cứu đồng thời giao dịch, ví và thông tin user theo mã payment_ref."""
    conn = get_db()
    if not conn:
        return jsonify({"error": "No connection"}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM shop_transactions WHERE payment_ref = %s", (ref,))
            row = cur.fetchone()
            if not row:
                return jsonify({"success": False, "error": f"Transaction {ref} not found"}), 404

            txn = dict(row)
            if "created_at" in txn:
                txn["created_at"] = str(txn["created_at"])
            if "updated_at" in txn:
                txn["updated_at"] = str(txn["updated_at"])

            wallet = None
            try:
                cur.execute("SELECT * FROM user_wallets WHERE user_id = %s", (txn["user_id"],))
                w_row = cur.fetchone()
                if w_row:
                    wallet = dict(w_row)
                    wallet["updated_at"] = str(wallet["updated_at"])
            except Exception as we:
                wallet = {"error_fetching_wallet": str(we)}

            user = None
            try:
                cur.execute(
                    "SELECT user_id, username, email FROM users WHERE user_id = %s",
                    (txn["user_id"],),
                )
                u_row = cur.fetchone()
                user = dict(u_row) if u_row else None
            except Exception as ue:
                user = {"error_fetching_user": str(ue)}

            return jsonify({
                "success": True,
                "transaction": txn,
                "wallet": wallet,
                "user": user,
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
