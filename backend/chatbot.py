from shared import app, sessions, gemini_client, GEMINI_MODEL, request, jsonify

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    """
    Xử lý tin nhắn chatbot bằng Gemini AI.
    Input: { "message": "...", "session_id": "..." }
    Output: { "reply": "..." }
    """
    data = request.get_json()
    message = data.get('message', '')
    session_id = data.get('session_id', '')

    # Lấy thông tin phiên chơi (nếu có)
    session = sessions.get(session_id, {})
    player_name = session.get('player_name', 'bạn')
    current = session.get('current_question', 0)
    
    if not gemini_client:
        return jsonify({'success': True, 'reply': "⚠️ Lỗi: Chưa cấu hình GEMINI_API_KEY trong file .env hoặc hệ thống nên chatbot đang bị vô hiệu hóa."})

    try:
        # Xây dựng prompt cung cấp ngữ cảnh trò chơi cho Gemini đóng vai
        # NGUYÊN LÝ HOÀN ĐỘNG (Prompt Chatbot):
        # 1. Cung cấp Context (Ngữ cảnh): Đưa tên người chơi và vị trí câu hiện tại vào để AI trả lời cá nhân hóa.
        # 2. Thiết lập Nhân cách (Persona): Đóng vai MC vui vẻ, thân thiện, động viên.
        # 3. Ràng buộc Logic (Constraints): Tuyệt đối KHÔNG lộ đáp án (để game luôn công bằng).
        # 4. Điều tiết độ dài: Yêu cầu trả lời ngắn gọn (< 3 câu) để giao diện chat không bị tràn.
        prompt = f'''Bạn là MC Trợ Lý ảo của trò chơi "Ai Là Triệu Phú". 
Tên người chơi là: {player_name}. Người chơi đang ở câu hỏi số {current + 1}/15.
Luật trò chơi: Có 15 câu hỏi, 3 quyền trợ giúp (50:50, Gọi ĐT, Hỏi khán giả), 2 mốc an toàn ở câu 5 và câu 10.

Câu hỏi/tin nhắn của người chơi: "{message}"

Nhiệm vụ: Trả lời người chơi bằng giọng điệu vui vẻ, tự nhiên, thân thiện và động viên họ. 
QUAN TRỌNG: KHÔNG ĐƯỢC để lộ đáp án đúng của bất kỳ câu hỏi nào nếu họ yêu cầu gợi ý (hãy khuyên họ dùng quyền trợ giúp).
Hãy trả lời ngắn gọn, súc tích (dưới 3 câu).'''

        # Gọi Gemini API để sinh câu trả lời
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        reply = response.text

    except Exception as e:
        print('Lỗi Gemini chatbot:', e)
        reply = f'Xin lỗi, tôi đang gặp trục trặc hệ thống. Vui lòng thử lại!'

    return jsonify({'success': True, 'reply': reply})