from shared import app, get_db, send_email_code, session, request, jsonify, psycopg2, random, datetime, timedelta

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'success': False, 'error': 'Vui lòng nhập email!'})

    conn = get_db()
    if not conn: return jsonify({'success': False, 'error': 'Lỗi database!'}), 500
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Tìm username theo email
            cur.execute("SELECT user_id, username FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if not user:
                return jsonify({'success': False, 'error': 'Email này chưa được đăng ký!'})
            
            # Tạo mã 6 số
            code = str(random.randint(100000, 999999))
            expires_at = datetime.now() + timedelta(minutes=15)
            
            # Lưu mã vào database
            cur.execute("""
                INSERT INTO password_reset_codes (user_id, code, expires_at)
                VALUES (%s, %s, %s)
            """, (user['user_id'], code, expires_at))
            conn.commit()
            
            # Gửi email
            if send_email_code(email, code):
                return jsonify({'success': True, 'message': 'Mã xác nhận đã được gửi tới email của bạn!'})
            else:
                return jsonify({'success': False, 'error': 'Không thể gửi email. Vui lòng kiểm tra lại cấu hình server.'})
                
    except Exception as e:
        if conn: conn.rollback()
        print(f"Lỗi forgot-password: {e}")
        return jsonify({'success': False, 'error': 'Lỗi máy chủ nội bộ!'}), 500
    finally:
        if conn: pass

# === API: Quên mật khẩu - Bước 2: Xác thực & Đặt lại ===
@app.route('/api/auth/verify-reset-code', methods=['POST'])
def verify_reset_code():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()
    new_password = data.get('new_password', '')

    if not email or not code or not new_password:
        return jsonify({'success': False, 'error': 'Vui lòng điền đầy đủ thông tin!'})

    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Tìm user
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if not user: return jsonify({'success': False, 'error': 'Lỗi xác minh!'})
            
            # Kiểm tra mã mới nhất cho user này
            cur.execute("""
                SELECT code_id FROM password_reset_codes 
                WHERE user_id = %s AND code = %s AND is_used = FALSE AND expires_at > NOW()
                ORDER BY created_at DESC LIMIT 1
            """, (user['user_id'], code))
            
            if not cur.fetchone():
                return jsonify({'success': False, 'error': 'Mã xác nhận không đúng hoặc đã hết hạn!'})
            
            # Cập nhật mật khẩu
            new_hash = hash_password(new_password)
            cur.execute("UPDATE user_passwords SET password_hash = %s WHERE user_id = %s", (new_hash, user['user_id']))
            
            # Đánh dấu mã đã dùng
            cur.execute("UPDATE password_reset_codes SET is_used = TRUE WHERE user_id = %s AND code = %s", (user['user_id'], code))
            
            conn.commit()
            return jsonify({'success': True, 'message': 'Đổi mật khẩu thành công!'})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'error': 'Lỗi hệ thống!'}), 500
    finally:
        if conn: pass