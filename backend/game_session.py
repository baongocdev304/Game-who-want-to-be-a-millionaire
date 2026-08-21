from shared import app, get_db, get_or_create_wallet, sessions, PRIZE_LEVELS, MILESTONES, gemini_client, GEMINI_MODEL, session, request, jsonify, psycopg2, uuid, time, json, random, generate_questions_with_ai, get_local_fallback_questions

@app.route('/api/game/start', methods=['POST'])
def start_game():
    """
    Tạo phiên chơi mới khi người chơi bấm "Bắt đầu".
    Input: { "player_name": "Tên người chơi" }
    Output: { "session_id": "...", "question": {...}, ... }
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Bạn chưa đăng nhập!'}), 401

    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Lỗi kết nối database!'}), 500
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            wallet = get_or_create_wallet(cur, user_id)
            if wallet['game_turns'] <= 0:
                return jsonify({'success': False, 'error': 'Bạn đã hết lượt chơi! Vui lòng vào Cửa hàng để mua thêm lượt.'})
            # Giảm 1 lượt chơi
            cur.execute("""
                UPDATE user_wallets
                SET game_turns = game_turns - 1, updated_at = NOW()
                WHERE user_id = %s
            """, (user_id,))
            conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'error': f'Lỗi hệ thống ví: {str(e)}'}), 500
    finally:
        if conn: pass

    # Lấy dữ liệu từ request
    data = request.get_json()
    player_name = data.get('player_name', 'Người chơi')

    # Tạo ID duy nhất cho phiên chơi
    session_id = str(uuid.uuid4())

    # Mức 1: Sinh câu hỏi qua AI trực tiếp (hướng Việt Nam thuần, 1-5 dễ, 6-10 trung bình, 11-15 khó)
    game_questions = generate_questions_with_ai()
    
    # Mức 2: Nếu AI lỗi (hết quota, mất mạng), dùng bộ câu hỏi offline thuần Việt được chuẩn bị sẵn
    if not game_questions:
        print("Tín hiệu mạng kém hoặc lỗi AI, sử dụng bộ câu hỏi dự phòng offline...")
        game_questions = get_local_fallback_questions()



    # Lưu phiên chơi vào bộ nhớ
    sessions[session_id] = {
        'user_id': session.get('user_id'),    # Lưu user_id để sau này ghi history
        'player_name': player_name,           # Tên người chơi
        'questions': game_questions,          # 15 câu hỏi đã chọn
        'current_question': 0,               # Câu hỏi hiện tại (0-14)
        'lifelines': {                        # Quyền trợ giúp còn không
            '5050': True,
            'phone': True,
            'audience': True
        },
        'start_time': time.time(),            # Thời điểm bắt đầu
        'total_time': 0,                      # Tổng thời gian
        'is_active': True,                    # Phiên đang hoạt động
        'prize': '0 đ'                        # Tiền thưởng hiện tại
    }

    # Lấy câu hỏi đầu tiên (ẩn đáp án đúng)
    first_q = game_questions[0].copy()
    del first_q['correct']  # Không gửi đáp án đúng cho frontend!

    # Trả về dữ liệu cho frontend
    return jsonify({
        'success': True,
        'session_id': session_id,
        'player_name': player_name,
        'question': first_q,
        'question_number': 1,
        'total_questions': 15,
        'prize_levels': PRIZE_LEVELS,
        'current_prize': '0 đ',
        'milestones': MILESTONES
    })

def record_game_result(user_id, result, score, duration, metadata=None):
    """Ghi lại kết quả ván chơi vào Postgres."""
    if not user_id: return
    conn = get_db()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO game_history (user_id, game_mode, result, score, duration_sec, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, 'solo', result, score, duration, json.dumps(metadata) if metadata else None))
            
            # Cập nhật rankings
            cur.execute("SELECT ranking_id FROM rankings WHERE user_id = %s", (user_id,))
            if cur.fetchone():
                if result == 'win':
                    cur.execute("UPDATE rankings SET total_wins = total_wins + 1, total_score = total_score + %s WHERE user_id = %s", (score, user_id))
                else:
                    cur.execute("UPDATE rankings SET total_losses = total_losses + 1, total_score = total_score + %s WHERE user_id = %s", (score, user_id))
            else:
                 cur.execute("""
                    INSERT INTO rankings (user_id, total_wins, total_losses, total_score)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, 1 if result == 'win' else 0, 1 if result == 'loss' else 0, score))
            conn.commit()
    except Exception as e:
        print(f"Lỗi khi ghi lịch sử: {e}")
        conn.rollback()
    finally:
        pass