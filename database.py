"""
Tầng 1 — Infrastructure & Persistence (Database)
===========================================================
File: database.py
Mô tả: Quản lý PostgreSQL ThreadedConnectionPool, khởi tạo Schema (8 bảng),
       Indexes, Trigger tự động tính win_rate và dữ liệu mẫu.
"""

import os
import bcrypt
import psycopg2
from psycopg2 import extensions, pool
from dotenv import load_dotenv

load_dotenv()

db_pool = None


def init_pool(minconn: int = 1, maxconn: int = 20):
    """Khởi tạo PostgreSQL ThreadedConnectionPool (an toàn đa luồng)."""
    global db_pool
    if db_pool is not None:
        return db_pool

    try:
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            db_pool = pool.ThreadedConnectionPool(minconn, maxconn, dsn=db_url)
        else:
            db_pool = pool.ThreadedConnectionPool(
                minconn,
                maxconn,
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'millionaire'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', '123456'),
            )
        print("✅ Khởi tạo PostgreSQL Connection Pool thành công!")
    except Exception as e:
        db_pool = None
        print(f"❌ Lỗi khởi tạo database pool: {e}")

    return db_pool


def get_connection():
    """Lấy một kết nối còn sống từ Connection Pool."""
    global db_pool
    if db_pool is None:
        init_pool()
    if db_pool is None:
        return None

    try:
        conn = db_pool.getconn()
        # Nếu kết nối cũ đã bị đóng bởi server/timeout, loại bỏ và lấy kết nối mới
        if conn.closed != 0:
            db_pool.putconn(conn, close=True)
            conn = db_pool.getconn()
        return conn
    except Exception as e:
        print(f"❌ Lỗi lấy kết nối từ pool: {e}")
        return None


def release_connection(conn):
    """Trả kết nối về pool an toàn (tự rollback nếu transaction chưa hoàn tất)."""
    global db_pool
    if conn is None:
        return

    if db_pool is None:
        try:
            if not conn.closed:
                conn.close()
        except Exception:
            pass
        return

    try:
        if conn.closed:
            db_pool.putconn(conn, close=True)
            return

        if conn.info.transaction_status != extensions.TRANSACTION_STATUS_IDLE:
            conn.rollback()
        db_pool.putconn(conn)
    except Exception as e:
        print(f"⚠️ Lỗi khi trả kết nối về pool: {e}")
        try:
            db_pool.putconn(conn, close=True)
        except Exception:
            pass


def close_pool():
    """Đóng toàn bộ kết nối trong pool khi tắt ứng dụng."""
    global db_pool
    if db_pool is not None:
        try:
            db_pool.closeall()
        finally:
            db_pool = None


# ============================================================
# SQL SCHEMA: 8 BẢNG, INDEXES & TRIGGER
# ============================================================

SQL_CREATE_TABLE = """
-- 1. BẢNG USERS
CREATE TABLE IF NOT EXISTS users (
    user_id      SERIAL PRIMARY KEY,
    username     VARCHAR(50)  UNIQUE NOT NULL,
    email        VARCHAR(100) UNIQUE NOT NULL,
    full_name    VARCHAR(100),
    avatar_url   TEXT,
    is_active    BOOLEAN      DEFAULT TRUE,
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 2. BẢNG PASSWORDS (tách riêng để bảo mật)
CREATE TABLE IF NOT EXISTS user_passwords (
    password_id   SERIAL PRIMARY KEY,
    user_id       INT          UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    password_hash TEXT         NOT NULL,
    salt          VARCHAR(255),
    last_changed  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    must_change   BOOLEAN      DEFAULT FALSE
);

-- 3. BẢNG XẾP HẠNG
CREATE TABLE IF NOT EXISTS rankings (
    ranking_id   SERIAL PRIMARY KEY,
    user_id      INT          UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    total_score  INT          DEFAULT 0,
    total_wins   INT          DEFAULT 0,
    total_losses INT          DEFAULT 0,
    total_draws  INT          DEFAULT 0,
    win_rate     NUMERIC(5,2) DEFAULT 0.00,
    rank_title   VARCHAR(50)  DEFAULT 'Newcomer',
    rank_points  INT          DEFAULT 0,
    updated_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 4. BẢNG LỊCH SỬ CHƠI
CREATE TABLE IF NOT EXISTS game_history (
    history_id   SERIAL PRIMARY KEY,
    user_id      INT          NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    game_mode    VARCHAR(50),
    result       VARCHAR(10)  CHECK (result IN ('win', 'loss', 'draw')),
    score        INT          DEFAULT 0,
    duration_sec INT,
    opponent_id  INT          REFERENCES users(user_id),
    metadata     JSONB,
    played_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 5. BẢNG MÃ KHÔI PHỤC MẬT KHẨU
CREATE TABLE IF NOT EXISTS password_reset_codes (
    code_id      SERIAL PRIMARY KEY,
    user_id      INT          NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    code         VARCHAR(6)   NOT NULL,
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    expires_at   TIMESTAMP    NOT NULL,
    is_used      BOOLEAN      DEFAULT FALSE
);

-- 6. BẢNG VÍ CHI TIẾT (Lượt chơi & Trợ giúp)
CREATE TABLE IF NOT EXISTS user_wallets (
    user_id         INT          PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    game_turns      INT          DEFAULT 3,
    bonus_lifelines INT          DEFAULT 0,
    updated_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 7. BẢNG GIAO DỊCH CỬA HÀNG
CREATE TABLE IF NOT EXISTS shop_transactions (
    transaction_id SERIAL PRIMARY KEY,
    user_id        INT          NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    item_type      VARCHAR(50)  NOT NULL, -- 'game_turn' hoặc 'bonus_lifeline'
    quantity       INT          NOT NULL,
    total_price    INT          NOT NULL,
    payment_ref    VARCHAR(100) UNIQUE NOT NULL,
    status         VARCHAR(20)  DEFAULT 'pending', -- 'pending', 'paid', 'failed'
    created_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 8. BẢNG NHẬT KÝ WEBHOOK (DEBUG)
CREATE TABLE IF NOT EXISTS webhook_logs (
    log_id           SERIAL       PRIMARY KEY,
    received_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    ip_address       VARCHAR(50),
    headers          JSONB,
    payload          JSONB,
    is_authenticated BOOLEAN      DEFAULT FALSE,
    auth_step        VARCHAR(100),
    payment_ref      VARCHAR(100),
    matched          BOOLEAN      DEFAULT FALSE,
    error_message    TEXT,
    status_code      INT
);
"""

SQL_CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_rankings_score     ON rankings(total_score DESC);
CREATE INDEX IF NOT EXISTS idx_rankings_points    ON rankings(rank_points DESC);
CREATE INDEX IF NOT EXISTS idx_history_user       ON game_history(user_id);
CREATE INDEX IF NOT EXISTS idx_history_played_at  ON game_history(played_at DESC);
"""

SQL_CREATE_TRIGGER = """
CREATE OR REPLACE FUNCTION update_win_rate()
RETURNS TRIGGER AS $$
BEGIN
    IF (NEW.total_wins + NEW.total_losses + NEW.total_draws) > 0 THEN
        NEW.win_rate := ROUND(
            NEW.total_wins::NUMERIC /
            (NEW.total_wins + NEW.total_losses + NEW.total_draws) * 100, 2
        );
    END IF;
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_win_rate ON rankings;
CREATE TRIGGER trg_win_rate
BEFORE UPDATE ON rankings
FOR EACH ROW EXECUTE FUNCTION update_win_rate();
"""


def create_schema(conn):
    """Tạo toàn bộ bảng, indexes và trigger nếu chưa tồn tại."""
    with conn.cursor() as cur:
        cur.execute(SQL_CREATE_TABLE)
        cur.execute(SQL_CREATE_INDEXES)
        cur.execute(SQL_CREATE_TRIGGER)
    conn.commit()
    print("✅ Tạo schema thành công!")


def insert_sample_data(conn):
    """Thêm một user mẫu cùng password, ranking, ví và lịch sử chơi."""
    with conn.cursor() as cur:
        cur.execute("SELECT user_id FROM users WHERE username = %s", ("player01",))
        if cur.fetchone():
            print("ℹ️ Dữ liệu mẫu đã tồn tại (player01), bỏ qua bước này.")
            return

        cur.execute("""
            INSERT INTO users (username, email, full_name)
            VALUES (%s, %s, %s)
            RETURNING user_id
        """, ("player01", "player01@email.com", "Nguyen Van A"))
        user_id = cur.fetchone()[0]

        hashed = bcrypt.hashpw("SecurePass123".encode(), bcrypt.gensalt()).decode()
        cur.execute("""
            INSERT INTO user_passwords (user_id, password_hash)
            VALUES (%s, %s)
        """, (user_id, hashed))

        cur.execute("""
            INSERT INTO rankings (user_id, total_wins, total_losses, rank_title, rank_points)
            VALUES (%s, 5, 2, 'Bronze', 150)
        """, (user_id,))

        cur.execute("""
            INSERT INTO user_wallets (user_id, game_turns, bonus_lifelines)
            VALUES (%s, 3, 0)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id,))

        sample_games = [
            (user_id, "pvp",  "win",  150, 320),
            (user_id, "solo", "loss", 80,  180),
            (user_id, "pvp",  "win",  200, 410),
        ]
        cur.executemany("""
            INSERT INTO game_history (user_id, game_mode, result, score, duration_sec)
            VALUES (%s, %s, %s, %s, %s)
        """, sample_games)

    conn.commit()
    print(f"✅ Đã thêm dữ liệu mẫu cho user_id={user_id}")


def main():
    conn = get_connection()
    if not conn:
        return

    try:
        create_schema(conn)
        insert_sample_data(conn)
        print("✅ Toàn bộ quá trình khởi tạo đã hoàn tất!")
    finally:
        release_connection(conn)
        close_pool()


if __name__ == '__main__':
    main()
