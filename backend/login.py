from shared import app, get_db, check_password, login_required, session, request, jsonify, redirect, render_template, psycopg2

@app.route('/api/auth/login', methods=['POST'])

def login():
    data = request.get_json()
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')

    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Lỗi kết nối database!'}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT u.user_id, u.username, u.full_name, p.password_hash 
                FROM users u 
                JOIN user_passwords p ON u.user_id = p.user_id
                WHERE u.username = %s
            """, (username,))
            user = cur.fetchone()

            if not user:
                return jsonify({'success': False, 'error': 'Tên đăng nhập không tồn tại!'})
            
            if not check_password(password, user['password_hash']):
                return jsonify({'success': False, 'error': 'Mật khẩu không đúng!'})

            session['username'] = user['username']
            session['user_id'] = user['user_id']
            session['display_name'] = user['full_name']
            return jsonify({'success': True, 'display_name': user['full_name']})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Lỗi hệ thống: {str(e)}'}), 500
    finally:
        if conn: pass


@app.route('/api/auth/me', methods=['GET'])
def me():
    if 'username' in session:
        return jsonify({'logged_in': True, 'username': session['username'], 'display_name': session['display_name']})
    return jsonify({'logged_in': False})

@app.route('/')
@login_required
def index():
    """Chỉ vào được nếu đã đăng nhập"""
    return render_template('index.html')

@app.route('/auth')
def auth_page():
    """Trang đăng nhập / đăng ký"""
    if 'username' in session:
        return redirect('/')
    return render_template('signin.html')