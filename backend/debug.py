from shared import app, get_db, request, jsonify, psycopg2

APP_VERSION = "v3-regex-fix-20260530"

@app.route('/api/debug/status', methods=['GET'])
def debug_status():
    """Endpoint chẩn đoán: kiểm tra phiên bản code, DB, và regex."""
    import re
    result = {
        'version': APP_VERSION,
        'db_connected': False,
        'tables_exist': False,
        'regex_test': None,
        'recent_transactions': []
    }
    # Test DB
    conn = get_db()
    if conn:
        result['db_connected'] = True
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT COUNT(*) FROM shop_transactions")
                result['tables_exist'] = True
                count = cur.fetchone()[0]
                # Lấy 5 giao dịch gần nhất
                cur.execute("""
                    SELECT payment_ref, status, item_type, quantity, total_price, created_at
                    FROM shop_transactions
                    ORDER BY created_at DESC LIMIT 5
                """)
                for row in cur.fetchall():
                    result['recent_transactions'].append({
                        'ref': row['payment_ref'],
                        'status': row['status'],
                        'item': row['item_type'],
                        'qty': row['quantity'],
                        'price': row['total_price'],
                        'created': str(row['created_at'])
                    })
        except Exception as e:
            result['db_error'] = str(e)
        finally:
            pass
    
    # Test regex against sample content
    test_content = "NHAN TU 06300420066666 TRACE 440721 ND AMT1780089184466B9A"
    match = re.search(r'AMT[\s_-]?(\d{10})[\s_-]?([A-Z0-9]{6})', test_content, re.IGNORECASE)
    if match:
        result['regex_test'] = {
            'input': test_content,
            'matched': True,
            'payment_ref': f"AMT_{match.group(1)}_{match.group(2).upper()}"
        }
    else:
        result['regex_test'] = {
            'input': test_content,
            'matched': False
        }
    
    return jsonify(result)

# === API: LỊCH SỬ WEBHOOK (DEBUG) ===
@app.route('/api/debug/webhooks', methods=['GET'])
def debug_webhooks():
    """Endpoint chẩn đoán: hiển thị danh sách nhật ký webhook gần đây."""
    result = {
        'db_connected': False,
        'logs': []
    }
    conn = get_db()
    if conn:
        result['db_connected'] = True
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT log_id, received_at, ip_address, headers, payload, 
                           is_authenticated, auth_step, payment_ref, matched, error_message, status_code
                    FROM webhook_logs
                    ORDER BY received_at DESC LIMIT 20
                """)
                for row in cur.fetchall():
                    result['logs'].append({
                        'id': row['log_id'],
                        'time': str(row['received_at']),
                        'ip': row['ip_address'],
                        'headers': row['headers'],
                        'payload': row['payload'],
                        'auth': row['is_authenticated'],
                        'auth_step': row['auth_step'],
                        'ref': row['payment_ref'],
                        'matched': row['matched'],
                        'error': row['error_message'],
                        'status': row['status_code']
                    })
        except Exception as e:
            result['db_error'] = str(e)
        finally:
            pass
    return jsonify(result)

# === API: CHI TIẾT GIAO DỊCH (DEBUG) ===
@app.route('/api/debug/transaction/<ref>', methods=['GET'])
def debug_transaction(ref):
    """Endpoint chẩn đoán: xem chi tiết trạng thái của giao dịch và ví."""
    conn = get_db()
    if not conn:
        return jsonify({'error': 'No connection'}), 500
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM shop_transactions WHERE payment_ref = %s", (ref,))
            row = cur.fetchone()
            if row:
                txn = dict(row)
                txn['created_at'] = str(txn['created_at'])
                txn['updated_at'] = str(txn['updated_at'])
                
                wallet = None
                try:
                    cur.execute("SELECT * FROM user_wallets WHERE user_id = %s", (txn['user_id'],))
                    w_row = cur.fetchone()
                    wallet = dict(w_row) if w_row else None
                    if wallet:
                        wallet['updated_at'] = str(wallet['updated_at'])
                except Exception as we:
                    wallet = {'error_fetching_wallet': str(we)}
                
                user = None
                try:
                    cur.execute("SELECT user_id, username, email FROM users WHERE user_id = %s", (txn['user_id'],))
                    u_row = cur.fetchone()
                    user = dict(u_row) if u_row else None
                except Exception as ue:
                    user = {'error_fetching_user': str(ue)}
                
                return jsonify({
                    'success': True,
                    'transaction': txn,
                    'wallet': wallet,
                    'user': user
                })
            else:
                return jsonify({'success': False, 'error': f'Transaction {ref} not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        pass