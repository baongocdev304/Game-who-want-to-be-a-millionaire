from shared import app, get_db, request, jsonify, psycopg2

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Lấy bảng xếp hạng top 10 từ database."""
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT u.full_name as player_name, r.total_score as score, r.total_wins as wins
                FROM rankings r
                JOIN users u ON r.user_id = u.user_id
                ORDER BY r.total_score DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            return jsonify({'success': True, 'leaderboard': [dict(row) for row in rows]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        pass