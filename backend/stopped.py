from shared import app, sessions, PRIZE_LEVELS, request, jsonify, time
from game_session import record_game_result

@app.route('/api/game/stop', methods=['POST'])
def stop_game():
    """Xử lý khi người chơi quyết định dừng cuộc chơi."""
    data = request.get_json()
    session_id = data.get('session_id')

    if session_id not in sessions:
        return jsonify({'success': False, 'error': 'Phiên không tồn tại'}), 404

    session = sessions[session_id]
    session['is_active'] = False
    session['total_time'] = int(time.time() - session['start_time'])

    current = session['current_question']
    prize = PRIZE_LEVELS[current - 1] if current > 0 else '0 đ'

    # Ghi vào DB
    score = int(prize.replace('.', '').replace(' đ', '')) if (prize != '0 đ') else 0
    record_game_result(session.get('user_id'), 'loss', score, session['total_time'])

    return jsonify({
        'success': True,
        'prize': prize,
        'correct_count': current,
        'total_time': session['total_time']
    })