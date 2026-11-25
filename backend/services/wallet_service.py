"""
Tầng 2B — Wallet Service
===========================================================
File: backend/services/wallet_service.py
Mô tả: Nghiệp vụ quản lý ví người chơi (game_turns, bonus_lifelines) đảm bảo atomic.
"""


def get_or_create_wallet(cur, user_id: int) -> dict:
    """Lấy hoặc tạo ví mặc định (3 lượt chơi, 0 trợ giúp) tránh race condition."""
    cur.execute(
        """
        INSERT INTO user_wallets (user_id, game_turns, bonus_lifelines)
        VALUES (%s, 3, 0)
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user_id,),
    )
    cur.execute(
        "SELECT game_turns, bonus_lifelines FROM user_wallets WHERE user_id = %s",
        (user_id,),
    )
    row = cur.fetchone()
    if row:
        return dict(row)

    raise ValueError(f"User ID {user_id} không tồn tại trong hệ thống.")


def deduct_game_turn(cur, user_id: int) -> tuple[bool, str | None]:
    """Kiểm tra và trừ 1 lượt chơi trong ví."""
    wallet = get_or_create_wallet(cur, user_id)
    if wallet["game_turns"] <= 0:
        return False, "Bạn đã hết lượt chơi! Vui lòng vào Cửa hàng để mua thêm lượt."

    cur.execute(
        """
        UPDATE user_wallets
        SET game_turns = game_turns - 1, updated_at = NOW()
        WHERE user_id = %s
        """,
        (user_id,),
    )
    return True, None


def deduct_bonus_lifeline(cur, user_id: int) -> tuple[bool, str | None]:
    """Kiểm tra và trừ 1 lượt trợ giúp dự phòng trong ví."""
    wallet = get_or_create_wallet(cur, user_id)
    if wallet["bonus_lifelines"] <= 0:
        return False, "Quyền trợ giúp đã hết và bạn không còn lượt trợ giúp dự phòng!"

    cur.execute(
        """
        UPDATE user_wallets
        SET bonus_lifelines = bonus_lifelines - 1, updated_at = NOW()
        WHERE user_id = %s
        """,
        (user_id,),
    )
    return True, None


def credit_wallet(cur, user_id: int, item_type: str, quantity: int):
    """Cộng vật phẩm (game_turn / bonus_lifeline) vào user_wallets (+ đồng bộ cột legacy nếu có)."""
    get_or_create_wallet(cur, user_id)

    if item_type == "game_turn":
        cur.execute(
            """
            UPDATE user_wallets
            SET game_turns = game_turns + %s, updated_at = NOW()
            WHERE user_id = %s
            """,
            (quantity, user_id),
        )
    elif item_type == "bonus_lifeline":
        cur.execute(
            """
            UPDATE user_wallets
            SET bonus_lifelines = bonus_lifelines + %s, updated_at = NOW()
            WHERE user_id = %s
            """,
            (quantity, user_id),
        )
    else:
        raise ValueError(f"Loại vật phẩm không hợp lệ: {item_type}")

    # Dùng SAVEPOINT để tránh làm hỏng transaction chính nếu bảng users không có cột legacy
    try:
        cur.execute("SAVEPOINT legacy_update")
        if item_type == "game_turn":
            cur.execute(
                "UPDATE users SET plays_left = plays_left + %s WHERE user_id = %s",
                (quantity, user_id),
            )
        elif item_type == "bonus_lifeline":
            cur.execute(
                "UPDATE users SET extra_lifelines = extra_lifelines + %s WHERE user_id = %s",
                (quantity, user_id),
            )
        cur.execute("RELEASE SAVEPOINT legacy_update")
    except Exception as e:
        cur.execute("ROLLBACK TO SAVEPOINT legacy_update")
        print(f"ℹ️ [Legacy] Bỏ qua cập nhật cột cũ trên bảng users: {e}")
