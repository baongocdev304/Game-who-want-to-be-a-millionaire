"""
Tầng 2B — Game Session Store & Result Persistence Service
===========================================================
File: backend/services/game_service.py
Mô tả:
- Quản lý trạng thái các phiên chơi đang diễn ra (GameSessionStore) — thiết kế giao diện
  độc lập để dễ dàng nâng cấp từ in-memory dict sang Redis/PostgreSQL khi chạy đa worker.
- Ghi nhận kết quả ván chơi vào bảng game_history và cập nhật bảng rankings.
"""

import json
import time
import uuid

from backend.core.extensions import get_db


class GameSessionStore:
    """Kho lưu trữ phiên chơi (hiện tại in-memory dict, tách riêng để dễ nâng cấp Redis)."""

    def __init__(self):
        self._sessions: dict[str, dict] = {}

    @property
    def sessions(self) -> dict[str, dict]:
        return self._sessions

    def create_session(self, user_id: int, player_name: str, questions: list[dict]) -> tuple[str, dict]:
        session_id = str(uuid.uuid4())
        game_sess = {
            "user_id": user_id,
            "player_name": player_name,
            "questions": questions,
            "current_question": 0,
            "lifelines": {
                "5050": True,
                "phone": True,
                "audience": True,
            },
            "start_time": time.time(),
            "total_time": 0,
            "is_active": True,
            "prize": 0,
        }
        self._sessions[session_id] = game_sess
        return session_id, game_sess

    def get_session(self, session_id: str | None) -> dict | None:
        if not session_id:
            return None
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str):
        self._sessions.pop(session_id, None)

    def clear(self):
        self._sessions.clear()


session_store = GameSessionStore()


def record_game_result(user_id: int | None, result: str, score: int, duration: int, metadata=None):
    """Ghi lại kết quả ván chơi vào game_history và cập nhật rankings."""
    if not user_id:
        return
    conn = get_db()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO game_history (user_id, game_mode, result, score, duration_sec, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    "solo",
                    result,
                    score,
                    duration,
                    json.dumps(metadata) if metadata else None,
                ),
            )

            cur.execute("SELECT ranking_id FROM rankings WHERE user_id = %s", (user_id,))
            if cur.fetchone():
                if result == "win":
                    cur.execute(
                        "UPDATE rankings SET total_wins = total_wins + 1, total_score = total_score + %s WHERE user_id = %s",
                        (score, user_id),
                    )
                else:
                    cur.execute(
                        "UPDATE rankings SET total_losses = total_losses + 1, total_score = total_score + %s WHERE user_id = %s",
                        (score, user_id),
                    )
            else:
                cur.execute(
                    """
                    INSERT INTO rankings (user_id, total_wins, total_losses, total_score)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        1 if result == "win" else 0,
                        1 if result == "loss" else 0,
                        score,
                    ),
                )
            conn.commit()
    except Exception as e:
        print(f"⚠️ Lỗi khi ghi lịch sử ván chơi: {e}")
        conn.rollback()
