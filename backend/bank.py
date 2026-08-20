from shared import app, get_db, get_or_create_wallet, login_required, SEPAY_BANK_CODE, SEPAY_ACCOUNT_NO, SEPAY_ACCOUNT_NAME, WEBHOOK_SECRET, session, request, jsonify, psycopg2, uuid, time, json, os, urllib

#Bank
def clean_env(val, default=""):
    if not val:
        return default
    # Loại bỏ comment nếu có (ví dụ: # comment)
    val = str(val).split('#')[0]
    return val.strip()

SEPAY_BANK_CODE    = clean_env(os.environ.get('SEPAY_BANK_CODE'), 'MBBank')      # Mã ngân hàng: VCB, TCB, MBBank, VPBank...
SEPAY_ACCOUNT_NO   = clean_env(os.environ.get('SEPAY_ACCOUNT_NO'), '0123456789') # Số tài khoản
SEPAY_ACCOUNT_NAME = clean_env(os.environ.get('SEPAY_ACCOUNT_NAME'), 'AI LA TRIEU PHU') # Tên chủ TK
WEBHOOK_SECRET     = clean_env(os.environ.get('WEBHOOK_SECRET'), 'dev-secret-123')

#Lấy thông tin ví
@app.route('/api/shop/wallet', methods=['GET'])
@login_required
def get_shop_wallet():
    user_id = session.get('user_id')
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Lỗi kết nối database!'}), 500
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            wallet = get_or_create_wallet(cur, user_id)
            conn.commit()
            return jsonify({
                'success': True,
                'game_turns': wallet['game_turns'],
                'bonus_lifelines': wallet['bonus_lifelines']
            })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: pass

@app.route('/api/shop/webhook', methods=['POST'])
@app.route('/api/webhook/sepay', methods=['POST'])
def shop_webhook():
    import hmac
    import hashlib
    import re
    import json

    data = request.get_json() or {}
    print(f"\n[SEPAY WEBHOOK] Nhận yêu cầu Webhook mới!")
    print(f" IP Người gọi: {request.remote_addr}")
    print(f" Payload nhận được: {data}")
    
    headers_dict = dict(request.headers)
    
    auth_info = {'step': 'Chưa xác thực', 'is_authenticated': False}
    payment_ref = None
    is_local = request.remote_addr in ['127.0.0.1', 'localhost', '::1']

    # Hàm hỗ trợ lưu nhật ký Webhook để phục vụ debug
    def log_webhook_attempt(is_auth, auth_step, ref, matched, error_msg, status_code):
        conn_log = get_db()
        if conn_log:
            try:
                with conn_log.cursor() as cur:
                    cur.execute("""
                        INSERT INTO webhook_logs (ip_address, headers, payload, is_authenticated, auth_step, payment_ref, matched, error_message, status_code)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        request.remote_addr,
                        json.dumps(headers_dict),
                        json.dumps(data),
                        is_auth,
                        auth_step,
                        ref,
                        matched,
                        error_msg,
                        status_code
                    ))
                conn_log.commit()
                print(" [Log Webhook] Đã lưu thông tin log webhook thành công!")
            except Exception as le:
                print(f" [Log Webhook] Không thể lưu log webhook: {le}")
            finally:
                conn_log.close()

    # Hàm hỗ trợ xác thực Webhook SePay
    def verify_sepay_request():
        webhook_secret = os.environ.get('WEBHOOK_SECRET', 'dev-secret-123').strip()
        print(f"🔒 [Xác thực SePay] Webhook secret cấu hình: {'***' + webhook_secret[-5:] if webhook_secret else 'TRỐNG'}")
        
        # 1. Xác thực bằng X-SePay-Signature header
        received_sig = request.headers.get('X-SePay-Signature')
        if received_sig:
            raw_body = request.get_data()
            computed_sig = hmac.new(
                webhook_secret.encode('utf-8'),
                raw_body,
                hashlib.sha256
            ).hexdigest()
            print(f" [Xác thực] Header X-SePay-Signature nhận được: {received_sig[:8]}...")
            print(f"[Xác thực] Chữ ký tính toán tương ứng: {computed_sig[:8]}...")
            if hmac.compare_digest(computed_sig, received_sig):
                print("[Xác thực] Chữ ký X-SePay-Signature hợp lệ!")
                auth_info['step'] = 'Header X-SePay-Signature'
                auth_info['is_authenticated'] = True
                return True
            else:
                auth_info['step'] = 'Header X-SePay-Signature (Sai chữ ký)'
                print(" [Xác thực] Chữ ký X-SePay-Signature không khớp!")
                
        # 2. Xác thực bằng Authorization: Apikey <secret> hoặc Bearer <secret>
        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split(' ')
            print(f"🔍 [Xác thực] Header Authorization: {parts[0]}")
            if len(parts) == 2 and parts[0].lower() in ['apikey', 'bearer']:
                print(f"🔍 [Xác thực] So khớp token: {parts[1][:5]}...")
                if hmac.compare_digest(parts[1], webhook_secret):
                    print(" [Xác thực] Token Authorization hợp lệ!")
                    auth_info['step'] = 'Header Authorization'
                    auth_info['is_authenticated'] = True
                    return True
                else:
                    auth_info['step'] = f"Header Authorization (Sai token: nhận {parts[1][:5]}...)"
                    print("[Xác thực] Token Authorization không khớp!")
                    
        # 3. Xác thực bằng X-API-Key hoặc X-Secret-Key
        api_key = request.headers.get('X-API-Key') or request.headers.get('X-Secret-Key')
        if api_key:
            print(f"🔍 [Xác thực] Header X-API-Key/X-Secret-Key nhận được: {api_key[:5]}...")
            if hmac.compare_digest(api_key, webhook_secret):
                print(" [Xác thực] API Key hợp lệ!")
                auth_info['step'] = 'Header X-API-Key/X-Secret-Key'
                auth_info['is_authenticated'] = True
                return True
            else:
                auth_info['step'] = f"Header X-API-Key/X-Secret-Key (Sai key: nhận {api_key[:5]}...)"
                print(" [Xác thực] API Key không khớp!")
                
        print(" [Xác thực] Tất cả phương thức xác thực SePay đều thất bại!")
        if auth_info['step'] == 'Chưa xác thực':
            auth_info['step'] = 'Không tìm thấy header xác thực hợp lệ'
        return False

    # Phân loại luồng Webhook dựa trên cấu trúc payload
    is_legacy = False
    legacy_user_id = None
    legacy_item_type = None

    if 'content' in data:
        print(" [Luồng Webhook] Nhận diện định dạng SePay chuẩn (chứa trường 'content')")
        is_authenticated = verify_sepay_request()
        if not is_authenticated and not is_local:
            print(" [Xác thực] Yêu cầu webhook SePay bị từ chối vì xác thực thất bại!")
            log_webhook_attempt(False, auth_info['step'], None, False, 'Xác thực Webhook SePay thất bại!', 401)
            return jsonify({'success': False, 'error': 'Xác thực Webhook SePay thất bại!'}), 401

        content = data.get('content', '').strip()
        print(f"📝 Nội dung chuyển khoản (Memo): '{content}'")
        
        # Hỗ trợ phản hồi thành công cho chức năng "Gửi thử" (Test Webhook) của SePay
        if 'sepay test' in content.lower() or data.get('code') == 'SEPAYTEST':
            print(" [Test Webhook] Nhận gói tin gửi thử thành công!")
            log_webhook_attempt(auth_info['is_authenticated'] or is_local, auth_info['step'] if not is_local else 'Local bypass', 'SEPAYTEST', True, None, 200)
            return jsonify({'success': True, 'message': 'Kết nối webhook thành công! (Test Webhook)'}), 200

        sepay_txn_id = data.get('id')
        try:
            transfer_amount = int(data.get('transferAmount', 0))
        except (ValueError, TypeError):
            transfer_amount = 0

        # 1.1 Kiểm tra xem có phải định dạng đơn hàng AMT_...
        # Hỗ trợ cả trường hợp có hoặc không có dấu gạch dưới '_', dấu cách hoặc dấu gạch ngang do ngân hàng/người dùng lọc bỏ
        # Sử dụng \d{10} (độ dài Unix timestamp) để tránh việc regex tham lam nuốt luôn chữ số đầu của phần mã hex ở đuôi.
        match_amt = re.search(r'AMT[\s_-]?(\d{10})[\s_-]?([A-Z0-9]{6})', content, re.IGNORECASE)
        if match_amt:
            payment_ref = f"AMT_{match_amt.group(1)}_{match_amt.group(2).upper()}"
            status = 'paid'
            print(f" [Regex] Trích xuất thành công mã đơn hàng: {payment_ref}")
        else:
            # 1.2 Kiểm tra xem có phải định dạng legacy ML/MT <user_id> (từ test_webhook.py)
            match_legacy = re.search(r'^(ML|MT)\s*(\d+)$', content, re.IGNORECASE)
            if match_legacy:
                type_prefix = match_legacy.group(1).upper()
                legacy_user_id = int(match_legacy.group(2))
                legacy_item_type = 'game_turn' if type_prefix == 'ML' else 'bonus_lifeline'
                is_legacy = True
                payment_ref = f"AMT_LEGACY_{sepay_txn_id}"
                status = 'paid'
                print(f" [Regex Legacy] Trích xuất legacy user_id={legacy_user_id}, loại={legacy_item_type}")
            else:
                print("[Lỗi] Nội dung chuyển khoản không chứa mã đơn hàng hợp lệ!")
                log_webhook_attempt(auth_info['is_authenticated'] or is_local, auth_info['step'] if not is_local else 'Local bypass', None, False, f"Nội dung chuyển khoản không chứa mã đơn hàng: '{content}'", 400)
                return jsonify({'success': False, 'error': 'Nội dung chuyển khoản không chứa mã đơn hàng hợp lệ!'}), 400
    else:
        print("📡 [Luồng Webhook] Nhận diện định dạng Giả lập (Simulator)")
        payment_ref = data.get('payment_ref')
        status = data.get('status')
        signature = data.get('signature')

        if not payment_ref or not status or not signature:
            print("[Lỗi] Định dạng giả lập thiếu tham số bắt buộc!")
            log_webhook_attempt(False, 'Simulator', payment_ref, False, 'Thiếu tham số bắt buộc!', 400)
            return jsonify({'success': False, 'error': 'Thiếu tham số bắt buộc!'}), 400

        # Xác minh chữ ký SHA256 HMAC cho luồng giả lập
        webhook_secret = os.environ.get('WEBHOOK_SECRET', 'dev-secret-123').encode('utf-8')
        msg = f"{payment_ref}:{status}".encode('utf-8')
        expected_sig = hmac.new(webhook_secret, msg, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_sig, signature):
            # Thử phương án dự phòng sử dụng 'dev-secret-123' cho môi trường phát triển
            fallback_sig = hmac.new(b'dev-secret-123', msg, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(fallback_sig, signature):
                print(" [Lỗi] Chữ ký giả lập không hợp lệ!")
                log_webhook_attempt(False, 'Simulator Signature Error', payment_ref, False, 'Chữ ký không hợp lệ!', 403)
                return jsonify({'success': False, 'error': 'Chữ ký không hợp lệ!'}), 403
        
        transfer_amount = None

    conn = get_db()
    if not conn:
        print("[Lỗi] Không thể kết nối tới cơ sở dữ liệu!")
        log_webhook_attempt(auth_info['is_authenticated'] or is_local, auth_info['step'] if not is_local else 'Local bypass', payment_ref, True, 'Lỗi kết nối database!', 500)
        return jsonify({'success': False, 'error': 'Lỗi kết nối database!'}), 500
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            if is_legacy:
                # Xử lý đặc biệt cho luồng legacy để tạo đơn tự động nếu chưa có
                cur.execute("""
                    SELECT user_id, item_type, quantity, total_price, status
                    FROM shop_transactions
                    WHERE payment_ref = %s
                """, (payment_ref,))
                txn = cur.fetchone()
                if not txn:
                    prices = {'game_turn': 5000, 'bonus_lifeline': 2000}
                    quantity = transfer_amount // prices[legacy_item_type]
                    if quantity <= 0:
                        print(" [Lỗi] Số tiền gửi không đủ mua sản phẩm!")
                        log_webhook_attempt(auth_info['is_authenticated'] or is_local, auth_info['step'] if not is_local else 'Local bypass', payment_ref, True, 'Số tiền gửi không đủ để mua lượt!', 400)
                        return jsonify({'success': False, 'error': 'Số tiền không đủ để mua lượt!'}), 400
                    
                    cur.execute("""
                        INSERT INTO shop_transactions (user_id, item_type, quantity, total_price, payment_ref, status)
                        VALUES (%s, %s, %s, %s, %s, 'pending')
                        RETURNING user_id, item_type, quantity, total_price, status
                    """, (legacy_user_id, legacy_item_type, quantity, transfer_amount, payment_ref))
                    txn = cur.fetchone()
            else:
                # Chỉ lấy các trường cần thiết để tương thích hoàn hảo với mọi cấu trúc cột khóa chính
                cur.execute("""
                    SELECT user_id, item_type, quantity, total_price, status
                    FROM shop_transactions
                    WHERE payment_ref = %s
                """, (payment_ref,))
                txn = cur.fetchone()
            
            if not txn:
                print(f" [Lỗi] Đơn hàng có mã {payment_ref} không tồn tại trong database!")
                log_webhook_attempt(auth_info['is_authenticated'] or is_local, auth_info['step'] if not is_local else 'Local bypass', payment_ref, True, 'Giao dịch không tồn tại trong database!', 404)
                return jsonify({'success': False, 'error': 'Giao dịch không tồn tại!'}), 404

            print(f" Tìm thấy đơn hàng trong Database: User={txn['user_id']}, Sản phẩm={txn['item_type']}, Số lượng={txn['quantity']}, Giá trị={txn['total_price']} đ, Trạng thái={txn['status']}")

            if txn['status'] == 'paid':
                print("ℹ Đơn hàng này đã được cộng vật phẩm thành công trước đó (bỏ qua).")
                log_webhook_attempt(auth_info['is_authenticated'] or is_local, auth_info['step'] if not is_local else 'Local bypass', payment_ref, True, 'Đơn hàng này đã được thanh toán rồi!', 200)
                return jsonify({'success': True, 'message': 'Giao dịch đã được thanh toán rồi!'})

            # Kiểm tra số tiền chuyển khoản của SePay thật (nếu có)
            if transfer_amount is not None and not is_legacy and transfer_amount < txn['total_price']:
                print(f"[Lỗi] Số tiền chuyển khoản không khớp! Đơn hàng: {txn['total_price']} đ, Chuyển thực tế: {transfer_amount} đ")
                log_webhook_attempt(auth_info['is_authenticated'] or is_local, auth_info['step'] if not is_local else 'Local bypass', payment_ref, True, f"Số tiền không khớp! Cần {txn['total_price']} đ nhưng nhận được {transfer_amount} đ", 400)
                return jsonify({'success': False, 'error': f"Số tiền không khớp! Cần {txn['total_price']} đ nhưng nhận được {transfer_amount} đ"}), 400

            if status == 'paid':
                # Cập nhật trạng thái
                cur.execute("""
                    UPDATE shop_transactions
                    SET status = 'paid'
                    WHERE payment_ref = %s
                """, (payment_ref,))

                # Đảm bảo người dùng có ví
                get_or_create_wallet(cur, txn['user_id'])

                # Cộng số lượng vật phẩm vào ví mới (user_wallets)
                if txn['item_type'] == 'game_turn':
                    cur.execute("""
                        UPDATE user_wallets
                        SET game_turns = game_turns + %s, updated_at = NOW()
                        WHERE user_id = %s
                    """, (txn['quantity'], txn['user_id']))
                elif txn['item_type'] == 'bonus_lifeline':
                    cur.execute("""
                        UPDATE user_wallets
                        SET bonus_lifelines = bonus_lifelines + %s, updated_at = NOW()
                        WHERE user_id = %s
                    """, (txn['quantity'], txn['user_id']))

                # Đồng thời cập nhật thêm bảng users cũ (nếu cột tồn tại)
                # QUAN TRỌNG: Phải dùng SAVEPOINT! Nếu query thất bại (cột không tồn tại),
                # PostgreSQL sẽ đánh dấu transaction "aborted" → conn.commit() sẽ ROLLBACK toàn bộ!
                try:
                    cur.execute("SAVEPOINT legacy_update")
                    if txn['item_type'] == 'game_turn':
                        cur.execute("UPDATE users SET plays_left = plays_left + %s WHERE user_id = %s", (txn['quantity'], txn['user_id']))
                    elif txn['item_type'] == 'bonus_lifeline':
                        cur.execute("UPDATE users SET extra_lifelines = extra_lifelines + %s WHERE user_id = %s", (txn['quantity'], txn['user_id']))
                    cur.execute("RELEASE SAVEPOINT legacy_update")
                except Exception as e:
                    # Rollback chỉ SAVEPOINT, không ảnh hưởng transaction chính
                    cur.execute("ROLLBACK TO SAVEPOINT legacy_update")
                    print(f"⚠️ [Legacy] Bỏ qua cập nhật bảng users cũ: {e}")
                
                conn.commit()
                log_webhook_attempt(auth_info['is_authenticated'] or is_local, auth_info['step'] if not is_local else 'Local bypass', payment_ref, True, None, 200)
                print(f"🎉 [Thành công] Đã cộng {txn['quantity']} {txn['item_type']} cho User_id={txn['user_id']}!")
                return jsonify({'success': True, 'message': 'Cộng vật phẩm thành công!'})
            else:
                cur.execute("""
                    UPDATE shop_transactions
                    SET status = %s
                    WHERE payment_ref = %s
                """, (status, payment_ref))
                conn.commit()
                log_webhook_attempt(auth_info['is_authenticated'] or is_local, auth_info['step'] if not is_local else 'Local bypass', payment_ref, True, None, 200)
                print(f" Cập nhật trạng thái đơn hàng {payment_ref} thành {status}")
                return jsonify({'success': True, 'message': f'Giao dịch được cập nhật thành {status}'})
    except Exception as e:
        if conn: conn.rollback()
        print(f" [Lỗi Hệ Thống] Exception trong shop_webhook: {str(e)}")
        log_webhook_attempt(auth_info['is_authenticated'] or is_local, auth_info['step'] if not is_local else 'Local bypass', payment_ref, False, f"Exception: {str(e)}", 500)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: pass
