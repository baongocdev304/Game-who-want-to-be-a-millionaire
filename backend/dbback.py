# dbback.py - Da duoc tich hop vao shared.py
# File nay khong can thiet nua, shared.py da co get_db, hash_password, login_required
# De tranh loi, cac file khac hay import tu shared.py thay vi dbback.py
from shared import (
    app, g, session, request, jsonify, redirect,
    get_connection, release_connection,
    bcrypt, wraps,
    get_db, get_or_create_wallet, hash_password, check_password, login_required
)

def get_db():
    if 'db' not in g:
        g.db = get_connection()
    return g.db

    if 'db' not in g:
        g.db = get_connection()
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        release_connection(db)

def get_or_create_wallet(cur, user_id):
    cur.execute("SELECT game_turns, bonus_lifelines FROM user_wallets WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    if row:
        return dict(row)
    else:
        # Kiểm tra xem user_id có tồn tại trong bảng users không
        cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cur.fetchone():
            raise ValueError(f"User ID {user_id} không tồn tại trong hệ thống.")
        cur.execute("""
            INSERT INTO user_wallets (user_id, game_turns, bonus_lifelines)
            VALUES (%s, 3, 0)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id,))
        return {'game_turns': 3, 'bonus_lifelines': 0}

def hash_password(pw):
    return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(pw, hashed):
    return bcrypt.checkpw(pw.encode('utf-8'), hashed.encode('utf-8'))


def login_required(f):
    """Decorator bảo vệ route - yêu cầu đăng nhập trước và kiểm tra user_id hợp lệ"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session or 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Vui lòng đăng nhập!'}), 401
            return redirect('/auth')

        user_id = session.get('user_id')
        conn = get_db()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
                    if not cur.fetchone():
                        session.clear()
                        if request.path.startswith('/api/'):
                            return jsonify({'success': False, 'error': 'Phiên đăng nhập hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại!'}), 401
                        return redirect('/auth')
            except Exception:
                pass

        return f(*args, **kwargs)
    return decorated
