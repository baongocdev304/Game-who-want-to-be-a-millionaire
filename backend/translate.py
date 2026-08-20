from shared import app, sessions, gemini_client, GEMINI_MODEL, request, jsonify, json

@app.route('/api/translate', methods=['POST'])
def translate_question():
    """
    Dịch câu hỏi hiện tại sang ngôn ngữ khác bằng Gemini API.
    Input: { "session_id": "...", "target_lang": "English" }
    Output: { "translated": { "question": "...", "answers": [...] } }
    """
    data = request.get_json()
    session_id = data.get('session_id')
    target_lang = data.get('target_lang', 'Tiếng Anh')
    
    if session_id not in sessions:
        return jsonify({'success': False, 'error': 'Phiên chơi không tồn tại'}), 404
        
    session = sessions[session_id]
    current = session['current_question']
    question = session['questions'][current]
    
    if not gemini_client:
         return jsonify({'success': False, 'error': 'Chưa cấu hình GEMINI_API_KEY'}), 500

    q_text = question['question']
    ans_texts = ', '.join(f"{chr(65+i)}: {ans}" for i, ans in enumerate(question['answers']))
    
    # Prompt yêu cầu AI trả về chuẩn JSON đã dịch
    prompt = f'''Dịch câu hỏi trắc nghiệm dưới đây sang {target_lang}.
Câu hỏi: {q_text}
Các đáp án: {ans_texts}
Trả về kết quả 100% dưới dạng chuỗi JSON nguyên gốc, KHÔNG BỌC trong markdown (chỉ format: {{"question": "câu hỏi đã dịch", "answers": ["dịch A", "dịch B", "dịch C", "dịch D"]}}), không thêm bất kỳ chữ nào khác.'''

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        res_text = response.text.strip()

        
        # Parse chuỗi JSON trả về
        if res_text.startswith("```json"): 
            res_text = res_text[7:]
        if res_text.startswith("```"):
            res_text = res_text[3:]
        if res_text.endswith("```"): 
            res_text = res_text[:-3]
            
        translated_data = json.loads(res_text.strip())
        return jsonify({'success': True, 'translated': translated_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def process_chatbot_message(msg, name, current_q):
    """
    Xử lý logic chatbot - phân tích tin nhắn và trả lời phù hợp.
    msg: nội dung tin nhắn (đã lowercase)
    name: tên người chơi
    current_q: câu hỏi hiện tại (0-14)
    """
