from shared import app, get_db, get_or_create_wallet, sessions, session, request, jsonify, psycopg2, random

@app.route('/api/game/lifeline', methods=['POST'])
def use_lifeline():
    """
    Xử lý khi người chơi dùng quyền trợ giúp.
    Input: { "session_id": "...", "type": "5050" | "phone" | "audience" }
    """
    data = request.get_json()
    session_id = data.get('session_id')
    lifeline_type = data.get('type')

    # Kiểm tra phiên
    if session_id not in sessions:
        return jsonify({'success': False, 'error': 'Phiên không tồn tại'}), 404

    session = sessions[session_id]

    # Kiểm tra quyền trợ giúp còn không
    if not session['lifelines'].get(lifeline_type, False):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Bạn chưa đăng nhập!'}), 401
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Lỗi kết nối database!'}), 500
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                wallet = get_or_create_wallet(cur, user_id)
                if wallet['bonus_lifelines'] <= 0:
                    return jsonify({'success': False, 'error': 'Quyền trợ giúp đã hết và bạn không còn lượt trợ giúp dự phòng!'})
                # Trừ 1 lượt trợ giúp trong ví
                cur.execute("""
                    UPDATE user_wallets
                    SET bonus_lifelines = bonus_lifelines - 1, updated_at = NOW()
                    WHERE user_id = %s
                """, (user_id,))
                conn.commit()
        except Exception as e:
            if conn: conn.rollback()
            return jsonify({'success': False, 'error': f'Lỗi hệ thống ví: {str(e)}'}), 500
        finally:
            if conn: pass
    else:
        # Đánh dấu đã dùng
        session['lifelines'][lifeline_type] = False

    # Lấy câu hỏi hiện tại
    question = session['questions'][session['current_question']]
    correct = question['correct']

    # === XỬ LÝ TỪNG LOẠI TRỢ GIÚP ===
    if lifeline_type == '5050':
        # 50:50: Loại 2 đáp án sai, giữ lại đáp án đúng + 1 sai
        wrong_indices = [i for i in range(4) if i != correct]
        random.shuffle(wrong_indices)
        removed = wrong_indices[:2]  # Loại 2 đáp án sai

        return jsonify({
            'success': True,
            'type': '5050',
            'removed': removed  # Danh sách index bị loại
        })

    elif lifeline_type == 'phone':
        # Gọi điện: 70% gợi ý đúng, 30% gợi ý sai
        is_right = random.random() < 0.7
        if is_right:
            suggestion = correct
            confidence = random.randint(70, 95)
        else:
            wrong = [i for i in range(4) if i != correct]
            suggestion = random.choice(wrong)
            confidence = random.randint(30, 60)

        return jsonify({
            'success': True,
            'type': 'phone',
            'suggestion': suggestion,      # Index đáp án gợi ý
            'confidence': confidence        # Phần trăm tự tin
        })

    elif lifeline_type == 'audience':
        # Hỏi khán giả: Tạo phân bố % ngẫu nhiên
        percents = [0, 0, 0, 0]
        # Đáp án đúng có % cao nhất
        percents[correct] = random.randint(35, 70)
        remaining = 100 - percents[correct]

        # Chia phần còn lại cho 3 đáp án sai
        for i in range(4):
            if i == correct:
                continue
            if remaining <= 0:
                percents[i] = 0
            else:
                p = random.randint(0, remaining)
                percents[i] = p
                remaining -= p

        # Đảm bảo tổng = 100
        diff = 100 - sum(percents)
        percents[correct] += diff

        return jsonify({
            'success': True,
            'type': 'audience',
            'percents': percents  # [%A, %B, %C, %D]
        })

    return jsonify({'success': False, 'error': 'Loại trợ giúp không hợp lệ'}), 400
