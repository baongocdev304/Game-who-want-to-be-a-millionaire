"""
Tầng 2A — Game & Shop Constants
===========================================================
File: backend/core/constants.py
Mô tả: Hằng số 15 mức tiền thưởng, mốc an toàn, giá vật phẩm cửa hàng,
       mẫu regex mã thanh toán và các hàm tính thưởng/định dạng tiền tệ.
"""

import re

# Regex trích xuất mã đơn hàng từ nội dung chuyển khoản SePay
AMT_REF_PATTERN = re.compile(r"AMT[\s_-]?(\d{10})[\s_-]?([A-Z0-9]{6})", re.IGNORECASE)
LEGACY_REF_PATTERN = re.compile(r"^(ML|MT)\s*(\d+)$", re.IGNORECASE)

# 15 mức tiền thưởng (đơn vị: VNĐ)
PRIZE_LEVELS = [
    200_000,       # Câu 1
    400_000,       # Câu 2
    600_000,       # Câu 3
    1_000_000,     # Câu 4
    2_000_000,     # Câu 5  ★ Mốc an toàn 1
    3_000_000,     # Câu 6
    6_000_000,     # Câu 7
    10_000_000,    # Câu 8
    14_000_000,    # Câu 9
    22_000_000,    # Câu 10 ★ Mốc an toàn 2
    30_000_000,    # Câu 11
    40_000_000,    # Câu 12
    60_000_000,    # Câu 13
    85_000_000,    # Câu 14
    150_000_000,   # Câu 15 ★ Mốc an toàn 3 (đích)
]

# Mốc an toàn (1-indexed: số câu đã vượt qua -> tiền giữ được)
MILESTONES = {
    5:  2_000_000,
    10: 22_000_000,
    15: 150_000_000,
}

# Bảng giá vật phẩm cửa hàng (đơn vị: VNĐ)
SHOP_PRICES = {
    "game_turn": 5000,
    "bonus_lifeline": 2000,
}


def format_prize(amount: int) -> str:
    """Chuyển số nguyên VNĐ sang chuỗi hiển thị (VD: 2000000 -> '2.000.000 đ')."""
    if amount == 0:
        return "0 đ"
    return f"{amount:,.0f}".replace(",", ".") + " đ"


def get_safe_prize(question_index: int) -> int:
    """Trả về số tiền thưởng ở mốc an toàn người chơi chắc chắn giữ được.

    question_index là chỉ số câu hiện tại (0-indexed = số câu đã trả lời đúng):
    - >= 15 -> 150.000.000 đ
    - >= 10 ->  22.000.000 đ
    - >= 5  ->   2.000.000 đ
    - < 5   ->           0 đ
    """
    if question_index >= 15:
        return 150_000_000
    if question_index >= 10:
        return 22_000_000
    if question_index >= 5:
        return 2_000_000
    return 0
