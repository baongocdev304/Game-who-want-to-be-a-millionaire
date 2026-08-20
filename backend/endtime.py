from shared import app, sessions, PRIZE_LEVELS, MILESTONES, request, jsonify, time
from game_session import record_game_result

@app.route('/api/game/timeout', methods=['POST'])
def timeout():
    """Xử lý khi người chơi hết thời gian trả lời."""
    data = request.get_json()
    session_id = data.get('session_id')

    if session_id not in sessions:
        return jsonify({'success': False, 'error': 'Phiên không tồn tại'}), 404

    session = sessions[session_id]
    session['is_active'] = False
    session['total_time'] = int(time.time() - session['start_time'])

    current = session['current_question']
    correct = session['questions'][current]['correct']

    # Tính tiền theo mốc an toàn
    safe_prize = '0 đ'
    for milestone in MILESTONES:
        if current > milestone:
            safe_prize = PRIZE_LEVELS[milestone]

    # Ghi vào DB
    score = int(safe_prize.replace('.', '').replace(' đ', '')) if (safe_prize != '0 đ') else 0
    record_game_result(session.get('user_id'), 'loss', score, session['total_time'])

    return jsonify({
        'success': True,
        'correct_answer': correct,
        'prize': safe_prize,
        'correct_count': current,
        'total_time': session['total_time']
    })