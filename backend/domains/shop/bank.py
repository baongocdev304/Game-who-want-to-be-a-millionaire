"""Shop/Payment Domain — Webhook tự động từ SePay VietQR & Simulator."""

import hashlib
import hmac
import json
import psycopg2.extras
from flask import current_app, jsonify, request

from backend.config import Config
from backend.core.constants import AMT_REF_PATTERN, LEGACY_REF_PATTERN, SHOP_PRICES
from backend.core.extensions import get_db, standalone_db_connection
from backend.domains.shop import shop_bp
from backend.services.wallet_service import credit_wallet


def _log_webhook_attempt(
    headers_dict: dict,
    data: dict,
    is_auth: bool,
    auth_step: str,
    ref: str | None,
    matched: bool,
    error_msg: str | None,
    status_code: int,
):
    """Lưu nhật ký webhook bằng kết nối DB độc lập để không bao giờ ảnh hưởng transaction chính."""
    try:
        with standalone_db_connection() as conn_log:
            if not conn_log:
                return
            with conn_log.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO webhook_logs (
                        ip_address, headers, payload, is_authenticated,
                        auth_step, payment_ref, matched, error_message, status_code
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        request.remote_addr,
                        json.dumps(headers_dict),
                        json.dumps(data),
                        is_auth,
                        auth_step,
                        ref,
                        matched,
                        error_msg,
                        status_code,
                    ),
                )
            conn_log.commit()
    except Exception as le:
        print(f"⚠️ [Log Webhook] Không thể lưu log webhook: {le}")


def _verify_sepay_request(webhook_secret: str, auth_info: dict) -> bool:
    """Xác thực request SePay qua 3 chuẩn header: X-SePay-Signature, Authorization, X-API-Key."""
    received_sig = request.headers.get("X-SePay-Signature")
    if received_sig:
        raw_body = request.get_data()
        computed_sig = hmac.new(
            webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        if hmac.compare_digest(computed_sig, received_sig):
            auth_info["step"] = "Header X-SePay-Signature"
            auth_info["is_authenticated"] = True
            return True
        auth_info["step"] = "Header X-SePay-Signature (Sai chữ ký)"

    auth_header = request.headers.get("Authorization")
    if auth_header:
        parts = auth_header.split(" ")
        if len(parts) == 2 and parts[0].lower() in ("apikey", "bearer"):
            if hmac.compare_digest(parts[1], webhook_secret):
                auth_info["step"] = "Header Authorization"
                auth_info["is_authenticated"] = True
                return True
            auth_info["step"] = f"Header Authorization (Sai token: nhận {parts[1][:5]}...)"

    api_key = request.headers.get("X-API-Key") or request.headers.get("X-Secret-Key")
    if api_key:
        if hmac.compare_digest(api_key, webhook_secret):
            auth_info["step"] = "Header X-API-Key/X-Secret-Key"
            auth_info["is_authenticated"] = True
            return True
        auth_info["step"] = f"Header X-API-Key/X-Secret-Key (Sai key: nhận {api_key[:5]}...)"

    if auth_info["step"] == "Chưa xác thực":
        auth_info["step"] = "Không tìm thấy header xác thực hợp lệ"
    return False


@shop_bp.route("/api/shop/webhook", methods=["POST"])
@shop_bp.route("/api/webhook/sepay", methods=["POST"])
def shop_webhook():
    """Nhận tín hiệu thanh toán từ SePay (hoặc Simulator) và cộng lượt/trợ giúp tự động."""
    data = request.get_json(silent=True) or {}
    headers_dict = dict(request.headers)
    webhook_secret = current_app.config.get("WEBHOOK_SECRET", Config.WEBHOOK_SECRET).strip()

    auth_info = {"step": "Chưa xác thực", "is_authenticated": False}
    payment_ref = None
    is_local = request.remote_addr in ("127.0.0.1", "localhost", "::1")

    def log_attempt(is_auth, step, ref, matched, err_msg, code):
        _log_webhook_attempt(headers_dict, data, is_auth, step, ref, matched, err_msg, code)

    is_legacy = False
    legacy_user_id = None
    legacy_item_type = None

    # 1. Phân loại luồng payload: SePay chuẩn (có trường 'content') vs Simulator
    if "content" in data:
        is_authenticated = _verify_sepay_request(webhook_secret, auth_info)
        if not is_authenticated and not is_local:
            log_attempt(False, auth_info["step"], None, False, "Xác thực Webhook SePay thất bại!", 401)
            return jsonify({"success": False, "error": "Xác thực Webhook SePay thất bại!"}), 401

        auth_flag = auth_info["is_authenticated"] or is_local
        auth_step = auth_info["step"] if auth_info["is_authenticated"] else "Local bypass"

        content = str(data.get("content", "")).strip()
        if "sepay test" in content.lower() or data.get("code") == "SEPAYTEST":
            log_attempt(auth_flag, auth_step, "SEPAYTEST", True, None, 200)
            return jsonify({"success": True, "message": "Kết nối webhook thành công! (Test Webhook)"}), 200

        sepay_txn_id = data.get("id")
        try:
            transfer_amount = int(data.get("transferAmount", 0))
        except (ValueError, TypeError):
            transfer_amount = 0

        match_amt = AMT_REF_PATTERN.search(content)
        if match_amt:
            payment_ref = f"AMT_{match_amt.group(1)}_{match_amt.group(2).upper()}"
            status = "paid"
        else:
            match_legacy = LEGACY_REF_PATTERN.search(content)
            if match_legacy:
                type_prefix = match_legacy.group(1).upper()
                legacy_user_id = int(match_legacy.group(2))
                legacy_item_type = "game_turn" if type_prefix == "ML" else "bonus_lifeline"
                is_legacy = True
                payment_ref = f"AMT_LEGACY_{sepay_txn_id}"
                status = "paid"
            else:
                log_attempt(
                    auth_flag,
                    auth_step,
                    None,
                    False,
                    f"Nội dung chuyển khoản không chứa mã đơn hàng: '{content}'",
                    400,
                )
                return jsonify({
                    "success": False,
                    "error": "Nội dung chuyển khoản không chứa mã đơn hàng hợp lệ!",
                }), 400
    else:
        payment_ref = data.get("payment_ref")
        status = data.get("status")
        signature = data.get("signature")

        if not payment_ref or not status or not signature:
            log_attempt(False, "Simulator", payment_ref, False, "Thiếu tham số bắt buộc!", 400)
            return jsonify({"success": False, "error": "Thiếu tham số bắt buộc!"}), 400

        msg = f"{payment_ref}:{status}".encode("utf-8")
        expected_sig = hmac.new(webhook_secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
        fallback_sig = hmac.new(b"dev-secret-123", msg, hashlib.sha256).hexdigest()

        sig_ok = hmac.compare_digest(expected_sig, signature) or (
            current_app.config.get("APP_ENV", Config.APP_ENV) != "production"
            and hmac.compare_digest(fallback_sig, signature)
        )
        if not sig_ok:
            log_attempt(False, "Simulator Signature Error", payment_ref, False, "Chữ ký không hợp lệ!", 403)
            return jsonify({"success": False, "error": "Chữ ký không hợp lệ!"}), 403

        auth_flag = True
        auth_step = "Simulator HMAC"
        transfer_amount = None

    # 2. Xử lý giao dịch trong PostgreSQL
    conn = get_db()
    if not conn:
        log_attempt(auth_flag, auth_step, payment_ref, True, "Lỗi kết nối database!", 500)
        return jsonify({"success": False, "error": "Lỗi kết nối database!"}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            if is_legacy:
                cur.execute(
                    """
                    SELECT user_id, item_type, quantity, total_price, status
                    FROM shop_transactions
                    WHERE payment_ref = %s
                    """,
                    (payment_ref,),
                )
                txn = cur.fetchone()
                if not txn:
                    quantity = transfer_amount // SHOP_PRICES[legacy_item_type]
                    if quantity <= 0:
                        log_attempt(auth_flag, auth_step, payment_ref, True, "Số tiền gửi không đủ để mua lượt!", 400)
                        return jsonify({"success": False, "error": "Số tiền không đủ để mua lượt!"}), 400

                    cur.execute(
                        """
                        INSERT INTO shop_transactions (user_id, item_type, quantity, total_price, payment_ref, status)
                        VALUES (%s, %s, %s, %s, %s, 'pending')
                        RETURNING user_id, item_type, quantity, total_price, status
                        """,
                        (legacy_user_id, legacy_item_type, quantity, transfer_amount, payment_ref),
                    )
                    txn = cur.fetchone()
            else:
                cur.execute(
                    """
                    SELECT user_id, item_type, quantity, total_price, status
                    FROM shop_transactions
                    WHERE payment_ref = %s
                    """,
                    (payment_ref,),
                )
                txn = cur.fetchone()

            if not txn:
                log_attempt(auth_flag, auth_step, payment_ref, True, "Giao dịch không tồn tại trong database!", 404)
                return jsonify({"success": False, "error": "Giao dịch không tồn tại!"}), 404

            # Idempotency check
            if txn["status"] == "paid":
                log_attempt(auth_flag, auth_step, payment_ref, True, "Đơn hàng này đã được thanh toán rồi!", 200)
                return jsonify({"success": True, "message": "Giao dịch đã được thanh toán rồi!"})

            if transfer_amount is not None and not is_legacy and transfer_amount < txn["total_price"]:
                err = f"Số tiền không khớp! Cần {txn['total_price']} đ nhưng nhận được {transfer_amount} đ"
                log_attempt(auth_flag, auth_step, payment_ref, True, err, 400)
                return jsonify({"success": False, "error": err}), 400

            if status == "paid":
                cur.execute(
                    """
                    UPDATE shop_transactions
                    SET status = 'paid'
                    WHERE payment_ref = %s
                    """,
                    (payment_ref,),
                )
                credit_wallet(cur, txn["user_id"], txn["item_type"], txn["quantity"])
                conn.commit()
                log_attempt(auth_flag, auth_step, payment_ref, True, None, 200)
                return jsonify({"success": True, "message": "Cộng vật phẩm thành công!"})

            cur.execute(
                """
                UPDATE shop_transactions
                SET status = %s
                WHERE payment_ref = %s
                """,
                (status, payment_ref),
            )
            conn.commit()
            log_attempt(auth_flag, auth_step, payment_ref, True, None, 200)
            return jsonify({"success": True, "message": f"Giao dịch được cập nhật thành {status}"})
    except Exception as e:
        conn.rollback()
        log_attempt(auth_flag, auth_step, payment_ref, False, f"Exception: {str(e)}", 500)
        return jsonify({"success": False, "error": str(e)}), 500
