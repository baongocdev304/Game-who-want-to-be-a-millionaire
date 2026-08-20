from shared import app, get_db, get_or_create_wallet, login_required, SEPAY_BANK_CODE, SEPAY_ACCOUNT_NO, SEPAY_ACCOUNT_NAME, session, request, jsonify, psycopg2, uuid, time, urllib

@app.route('/api/shop/create-order', methods=['POST'])
@login_required
def create_shop_order():
    data = request.get_json()
    item_type = data.get('item_type') # 'game_turn' hoặc 'bonus_lifeline'
    quantity = data.get('quantity')

    if item_type not in ['game_turn', 'bonus_lifeline'] or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'success': False, 'error': 'Dữ liệu không hợp lệ!'}), 400

    prices = {'game_turn': 5000, 'bonus_lifeline': 2000}
    total_price = prices[item_type] * quantity
    user_id = session.get('user_id')

    # Tạo mã thanh toán ngẫu nhiên
    payment_ref = f"AMT_{int(time.time())}_{uuid.uuid4().hex[:6].upper()}"

    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Lỗi kết nối database!'}), 500
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                INSERT INTO shop_transactions (user_id, item_type, quantity, total_price, payment_ref, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
            """, (user_id, item_type, quantity, total_price, payment_ref))
            conn.commit()
            # Tạo URL QR SePay (dùng VietQR — SePay hỗ trợ chuẩn này)
            qr_url = (
                f"https://img.vietqr.io/image/{SEPAY_BANK_CODE}-{SEPAY_ACCOUNT_NO}-compact2.png"
                f"?amount={total_price}&addInfo={urllib.parse.quote(payment_ref)}"
                f"&accountName={urllib.parse.quote(SEPAY_ACCOUNT_NAME)}"
            )
            return jsonify({
                'success': True,
                'txn_id': payment_ref,   # dùng payment_ref làm ID đơn
                'payment_ref': payment_ref,
                'total_price': total_price,
                'qr_url': qr_url,
                'bank_code': SEPAY_BANK_CODE,
                'account_no': SEPAY_ACCOUNT_NO,
                'account_name': SEPAY_ACCOUNT_NAME,
            })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: pass

# === API: KIỂM TRA TRẠNG THÁI ĐƠN HÀNG (POLLING) ===
@app.route('/api/shop/check-status', methods=['GET'])
@login_required
def check_order_status():
    payment_ref = request.args.get('ref')
    if not payment_ref:
        return jsonify({'success': False, 'error': 'Thiếu payment_ref'}), 400
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Lỗi kết nối database!'}), 500
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "SELECT status FROM shop_transactions WHERE payment_ref = %s",
                (payment_ref,)
            )
            row = cur.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Không tìm thấy giao dịch'}), 404
            return jsonify({'success': True, 'status': row['status']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: pass

# === API: LỊCH SỬ MUA HÀNG ===
@app.route('/api/shop/history', methods=['GET'])
@login_required
def get_shop_history():
    user_id = session.get('user_id')
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Lỗi kết nối database!'}), 500
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT item_type, quantity, total_price, payment_ref, status, created_at
                FROM shop_transactions
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 20
            """, (user_id,))
            rows = cur.fetchall()
            txns = []
            for r in rows:
                txn = dict(r)
                # Chuyển đổi datetime sang định dạng ISO cho JSON
                if txn.get('created_at'):
                    txn['created_at'] = txn['created_at'].isoformat()
                txns.append(txn)
            return jsonify({'success': True, 'transactions': txns})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: pass