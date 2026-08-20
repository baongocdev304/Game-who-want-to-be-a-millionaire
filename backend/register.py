from shared import app, get_db, hash_password, session, request, jsonify, psycopg2
#API Đăng nhập
@app.route('/api/auth/register', methods=['POST'])

def register():
    data = request.get_json()
    username = data.get('username', '').strip().lower()
    email = data.get('email', '').strip().lower() # Bắt buộc phải có email
    display_name = data.get('display_name', '').strip()
    password = data.get('password', '')

    if not username or not email or not password or not display_name:
        return jsonify({'success': False, 'error': 'Vui lòng điền đầy đủ tất cả các thông tin!'})
    
    if len(username) < 3:
        return jsonify({'success': False, 'error': 'Tên đăng nhập phải ít nhất 3 ký tự!'})
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Mật khẩu phải ít nhất 6 ký tự!'})

    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Lỗi kết nối database!'}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Kiểm tra tồn tại
            cur.execute("SELECT user_id FROM users WHERE username = %s OR email = %s", (username, email))
            if cur.fetchone():
                return jsonify({'success': False, 'error': 'Tên đăng nhập hoặc email đã tồn tại!'})

            # Thêm user
            cur.execute("""
                INSERT INTO users (username, email, full_name)
                VALUES (%s, %s, %s) RETURNING user_id
            """, (username, email, display_name))
            user_id = cur.fetchone()['user_id']

            # Thêm password
            hashed = hash_password(password)
            cur.execute("""
                INSERT INTO user_passwords (user_id, password_hash)
                VALUES (%s, %s)
            """, (user_id, hashed))

            # Khởi tạo rankings cho user mới
            cur.execute("""
                INSERT INTO rankings (user_id, total_score, total_wins, total_losses, rank_title, rank_points)
                VALUES (%s, 0, 0, 0, 'Newcomer', 0)
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id,))

            # Khởi tạo ví (lượt chơi) cho user mới
            cur.execute("""
                INSERT INTO user_wallets (user_id, game_turns, bonus_lifelines)
                VALUES (%s, 3, 0)
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id,))

            conn.commit()
            session['username'] = username
            session['user_id'] = user_id
            session['display_name'] = display_name
            return jsonify({'success': True})
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Lỗi register: {e}")
        return jsonify({'success': False, 'error': f'Lỗi hệ thống: {str(e)}'}), 500
    finally:
        pass  # Connection được Flask tự release qua teardown_appcontext

