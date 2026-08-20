from shared import app, get_db, login_required, session, request, jsonify, psycopg2

@app.route('/api/game/history', methods=['GET'])
@login_required
def get_user_history():
    user_id = session.get('user_id')
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT history_id, result, score, duration_sec, played_at 
                FROM game_history 
                WHERE user_id = %s 
                ORDER BY played_at DESC 
                LIMIT 20
            """, (user_id,))
            rows = cur.fetchall()
            history = [dict(row) for row in rows]
            return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        pass