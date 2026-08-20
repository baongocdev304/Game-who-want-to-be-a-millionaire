from shared import app, get_db, sessions, PRIZE_LEVELS, MILESTONES, session, request, jsonify, psycopg2, time, json, random, gemini_client, GEMINI_MODEL
from game_session import record_game_result

@app.route('/api/game/answer', methods=['POST'])
def answer_question():
    """
    Xử lý khi người chơi chọn đáp án.
    Input: { "session_id": "...", "answer": 0-3 }
    Output: { "is_correct": true/false, "correct_answer": 0-3, ... }
    """
    data = request.get_json()
    session_id = data.get('session_id')
    answer = data.get('answer')  # Index đáp án: 0=A, 1=B, 2=C, 3=D

    # Kiểm tra phiên chơi có tồn tại không
    if session_id not in sessions:
        return jsonify({'success': False, 'error': 'Phiên chơi không tồn tại'}), 404

    game_sess = sessions[session_id]  # Đổi tên để không ghi đè Flask session

    # Kiểm tra phiên còn hoạt động không
    if not game_sess['is_active']:
        return jsonify({'success': False, 'error': 'Phiên chơi đã kết thúc'}), 400

    # Lấy câu hỏi hiện tại
    current = game_sess['current_question']
    question = game_sess['questions'][current]
    correct_answer = question['correct']

    # Kiểm tra đúng/sai
    is_correct = (answer == correct_answer)

    if is_correct:
        # === TRẢ LỜI ĐÚNG ===
        game_sess['current_question'] += 1
        game_sess['prize'] = PRIZE_LEVELS[current]

        # Kiểm tra đã trả lời hết 15 câu chưa
        if game_sess['current_question'] >= 15:
            # THẮNG GAME!
            game_sess['is_active'] = False
            game_sess['total_time'] = int(time.time() - game_sess['start_time'])
            
            # Ghi vào DB
            record_game_result(game_sess.get('user_id'), 'win', 150000000, game_sess['total_time'])

            return jsonify({
                'success': True,
                'is_correct': True,
                'correct_answer': correct_answer,
                'game_over': True,
                'won': True,
                'prize': PRIZE_LEVELS[14],
                'correct_count': 15,
                'total_time': game_sess['total_time']
            })


        # Gửi câu hỏi tiếp theo
        next_q = game_sess['questions'][game_sess['current_question']].copy()
        del next_q['correct']  # Ẩn đáp án đúng

        return jsonify({
            'success': True,
            'is_correct': True,
            'correct_answer': correct_answer,
            'game_over': False,
            'next_question': next_q,
            'question_number': game_sess['current_question'] + 1,
            'current_prize': game_sess['prize']
        })
    else:
        # === TRẢ LỜI SAI ===
        game_sess['is_active'] = False
        game_sess['total_time'] = int(time.time() - game_sess['start_time'])

        # Tính tiền dựa trên mốc an toàn
        safe_prize = '0 đ'
        score = 0
        for milestone in MILESTONES:
            if current > milestone:
                safe_prize = PRIZE_LEVELS[milestone]
                # Parse số tiền (ví dụ "2.000.000 đ" -> 2000000)
                score = int(safe_prize.replace('.', '').replace(' đ', ''))

        # Ghi vào DB
        record_game_result(game_sess.get('user_id'), 'loss', score, game_sess['total_time'])

        return jsonify({
            'success': True,
            'is_correct': False,
            'correct_answer': correct_answer,
            'game_over': True,
            'won': False,
            'prize': safe_prize,
            'correct_count': current,
            'total_time': game_sess['total_time']
        })

# === SINH CÂU HỎI QUA AI TỰ ĐỘNG ===
def generate_questions_with_ai():
    """Dùng Gemini AI để tạo ra 15 câu hỏi mới theo độ khó tăng dần."""
    if not gemini_client:
        return None

    # NGUYÊN LÝ HOẠT ĐỘNG (Prompt Việt Hóa & Phân Loại Cực Kỳ Chi Tiết):
    # - Câu 1-5 (Dễ): Kiến thức thông thường ai người Việt cũng biết (bánh chưng, cổ tích, địa lý cơ bản).
    # - Câu 6-10 (Trung bình): Kiến thức phổ thông của người Việt trưởng thành.
    # - Câu 11-15 (Khó): Kiến thức sâu, lịch sử, toán logic học thuật.
    prompt = '''Bạn là một chuyên gia biên soạn câu hỏi cho gameshow "Ai Là Triệu Phú" phiên bản Việt Nam.
Nhiệm vụ: Sáng tác bộ đúng 15 câu hỏi trắc nghiệm tiếng Việt chất lượng cao. Các câu hỏi phải thuần Việt, gần gũi với đời sống, văn hóa, lịch sử, địa lý và kiến thức phổ thông của người Việt Nam.

Phân bổ độ khó và thứ tự xuất hiện bắt buộc:
- Từ câu 1 đến câu 5 (Độ khó: Dễ - "easy"): Những kiến thức cực kỳ cơ bản mà bất kỳ người Việt Nam nào cũng biết. Ví dụ: truyện cổ tích (Thạch Sanh, Thánh Gióng), món ăn truyền thống (bánh chưng, phở), địa lý cơ bản (thủ đô Việt Nam là gì),... Câu hỏi ngắn gọn, rõ ràng.
- Từ câu 6 đến câu 10 (Độ khó: Trung bình - "medium"): Kiến thức phổ thông rộng hơn về văn học Việt Nam, lịch sử Việt Nam, khoa học thường thức, địa lý tỉnh thành, danh lam thắng cảnh. Ở mức người lớn tuổi trung bình đều trả lời được.
- Từ câu 11 đến câu 15 (Độ khó: Khó - "hard"): Kiến thức chuyên sâu về lịch sử phong kiến, địa lý thế giới, khoa học vũ trụ, toán học logic hoặc sự kiện ít phổ biến. Câu hỏi đòi hỏi người chơi có kiến thức rất rộng mới trả lời được.

Yêu cầu kỹ thuật:
1. Trả về đúng 15 câu hỏi. Sắp xếp theo đúng thứ tự: 5 câu đầu có difficulty là "easy", 5 câu tiếp theo là "medium", 5 câu cuối là "hard".
2. Định dạng đầu ra phải là mảng JSON thuần túy, không có thẻ Markdown (không có ```json) hay bất kỳ văn bản giải thích nào xung quanh. Chỉ trả về chuỗi JSON bắt đầu bằng [ và kết thúc bằng ].
3. Cấu trúc mỗi câu hỏi:
   {"difficulty": "easy"|"medium"|"hard", "question": "Nội dung câu hỏi...", "answers": ["Đáp án A", "Đáp án B", "Đáp án C", "Đáp án D"], "correct": index_đáp_án_đúng_từ_0_đến_3}
'''
    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        res_text = "".join([part.text for part in response.candidates[0].content.parts if part.text])
        res_text = res_text.strip()
        
        # Lọc JSON
        start_idx = res_text.find('[')
        end_idx = res_text.rfind(']')
        if start_idx != -1 and end_idx != -1:
            res_text = res_text[start_idx:end_idx+1]
        
        parsed = json.loads(res_text)
        if type(parsed) is list and len(parsed) >= 15:
            return parsed[:15]
    except Exception as e:
        print("Lỗi từ AI trong việc sinh câu hỏi:", e)
    
    return None


# === BỘ CÂU HỎI DỰ PHÒNG THUẦN VIỆT (TRÁNH LỖI MẤT MẠNG HOÀN TOÀN) ===
LOCAL_EASY_QUESTIONS = [
    {"difficulty": "easy", "question": "Bánh chưng là món ăn truyền thống của Việt Nam vào dịp lễ nào?", "answers": ["Tết Đoan Ngọ", "Tết Trung Thu", "Tết Nguyên Đán", "Tết Thanh Minh"], "correct": 2},
    {"difficulty": "easy", "question": "Thủ đô của nước Cộng hòa Xã hội Chủ nghĩa Việt Nam là gì?", "answers": ["TP. Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Hà Nội"], "correct": 3},
    {"difficulty": "easy", "question": "Nhân vật Sơn Tinh trong truyền thuyết Sơn Tinh - Thủy Tinh đại diện cho điều gì?", "answers": ["Lũ lụt", "Núi đồi và trị thủy", "Gió bão", "Sét đánh"], "correct": 1},
    {"difficulty": "easy", "question": "Loài động vật nào sau đây nổi tiếng với thói quen gầm, được mệnh danh là chúa tể sơn lâm?", "answers": ["Sư tử", "Hổ", "Báo hoa mai", "Gấu"], "correct": 1},
    {"difficulty": "easy", "question": "Trong truyện cổ tích Tấm Cám, quả thị rụng vào giỏ của ai?", "answers": ["Cám", "Mẹ Cám", "Bà cụ hàng nước", "Tấm"], "correct": 2},
    {"difficulty": "easy", "question": "Tên nước Việt Nam dưới thời vua Đinh Tiên Hoàng là gì?", "answers": ["Đại Việt", "Đại Cồ Việt", "Văn Lang", "Âu Lạc"], "correct": 1},
    {"difficulty": "easy", "question": "Quốc kỳ Việt Nam có bao nhiêu ngôi sao ở giữa?", "answers": ["1 ngôi sao", "2 ngôi sao", "3 ngôi sao", "5 ngôi sao"], "correct": 0},
    {"difficulty": "easy", "question": "Hình ảnh trên tờ tiền 200.000 VNĐ của Việt Nam là danh lam thắng cảnh nào?", "answers": ["Chùa Một Cột", "Vịnh Hạ Long", "Phố cổ Hội An", "Hồ Hoàn Kiếm"], "correct": 1},
    {"difficulty": "easy", "question": "Trái Đất quay quanh thiên thể nào?", "answers": ["Mặt Trăng", "Mặt Trời", "Sao Hỏa", "Sao Kim"], "correct": 1},
    {"difficulty": "easy", "question": "Bộ phim hoạt hình 'Doraemon' có nguồn gốc từ quốc gia nào?", "answers": ["Hàn Quốc", "Trung Quốc", "Nhật Bản", "Mỹ"], "correct": 2},
    {"difficulty": "easy", "question": "Nhạc cụ dân tộc nào sau đây chỉ có một dây?", "answers": ["Đàn bầu", "Đàn tranh", "Đàn tì bà", "Đàn nhị"], "correct": 0},
    {"difficulty": "easy", "question": "Loài cây nào được dựng trước nhà ngày Tết để trừ tà ma theo quan niệm dân gian?", "answers": ["Cây tre", "Cây đào", "Cây nêu", "Cây mai"], "correct": 2},
    {"difficulty": "easy", "question": "Ai là người anh hùng nhỏ tuổi đã bóp nát quả cam vì không được dự hội nghị Diên Hồng?", "answers": ["Kim Đồng", "Trần Quốc Toản", "Võ Thị Sáu", "Lê Văn Tám"], "correct": 1},
    {"difficulty": "easy", "question": "Con vật nào là phương tiện di chuyển chính ở sa mạc?", "answers": ["Lạc đà", "Ngựa", "Lừa", "Voi"], "correct": 0},
    {"difficulty": "easy", "question": "Loài chim nào thường báo hiệu mùa xuân về ở Việt Nam?", "answers": ["Chim sẻ", "Chim én", "Chim bồ câu", "Chim họa mi"], "correct": 1}
]

LOCAL_MEDIUM_QUESTIONS = [
    {"difficulty": "medium", "question": "Nhà thơ nào được mệnh danh là 'Bà chúa thơ Nôm'?", "answers": ["Xuân Quỳnh", "Hồ Xuân Hương", "Đoàn Thị Điểm", "Bà Huyện Thanh Quan"], "correct": 1},
    {"difficulty": "medium", "question": "Sông nào dài nhất Việt Nam chảy hoàn toàn trong lãnh thổ quốc gia?", "answers": ["Sông Hồng", "Sông Đồng Nai", "Sông Đà", "Sông Mê Kông"], "correct": 1},
    {"difficulty": "medium", "question": "Chiến dịch Điện Biên Phủ kết thúc thắng lợi vào năm nào?", "answers": ["1945", "1954", "1975", "1986"], "correct": 1},
    {"difficulty": "medium", "question": "Tác phẩm kiệt tác 'Truyện Kiều' của Nguyễn Du được viết bằng chữ gì?", "answers": ["Chữ Quốc ngữ", "Chữ Hán", "Chữ Nôm", "Chữ Phạn"], "correct": 2},
    {"difficulty": "medium", "question": "Ai là người Việt Nam đầu tiên bay vào vũ trụ?", "answers": ["Phạm Tuân", "Bùi Thanh Liêm", "Trịnh Hữu Châu", "Nguyễn Văn Hùng"], "correct": 0},
    {"difficulty": "medium", "question": "Vùng đất Tây Nguyên nổi tiếng với loại cây công nghiệp xuất khẩu chủ lực nào sau đây?", "answers": ["Cây cao su", "Cây chè", "Cây cà phê", "Cây điều"], "correct": 2},
    {"difficulty": "medium", "question": "Nước Việt Nam nằm ở phía nào của bán đảo Đông Dương?", "answers": ["Phía Tây", "Phía Đông", "Phía Nam", "Phía Bắc"], "correct": 1},
    {"difficulty": "medium", "question": "Danh y Hải Thượng Lãn Ông tên thật là gì?", "answers": ["Tuệ Tĩnh", "Lê Hữu Trác", "Nguyễn Bỉnh Khiêm", "Chu Văn An"], "correct": 1},
    {"difficulty": "medium", "question": "Hồ nước ngọt tự nhiên lớn nhất thế giới xét theo thể tích là hồ nào?", "answers": ["Hồ Baikal", "Hồ Superior", "Hồ Victoria", "Hồ Michigan"], "correct": 0},
    {"difficulty": "medium", "question": "Mặt Trăng cách Trái Đất khoảng bao nhiêu ki-lô-mét?", "answers": ["150.000 km", "384.000 km", "1.000.000 km", "50.000 km"], "correct": 1},
    {"difficulty": "medium", "question": "Tỉnh nào của Việt Nam có diện tích tự nhiên lớn nhất?", "answers": ["Thanh Hóa", "Nghệ An", "Gia Lai", "Lâm Đồng"], "correct": 1},
    {"difficulty": "medium", "question": "Truyện ngắn 'Chí Phèo' của nhà văn Nam Cao ban đầu có tên là gì?", "answers": ["Cái lò gạch cũ", "Đôi mắt", "Lão Hạc", "Sống mòn"], "correct": 0},
    {"difficulty": "medium", "question": "Ai là người soạn thảo bản Tuyên ngôn Độc lập khai sinh ra nước Việt Nam Dân chủ Cộng hòa?", "answers": ["Phan Bội Châu", "Hồ Chí Minh", "Võ Nguyên Giáp", "Trường Chinh"], "correct": 1},
    {"difficulty": "medium", "question": "Kim loại nào dẫn điện tốt nhất trong các kim loại dưới đây?", "answers": ["Vàng", "Bạc", "Đồng", "Nhôm"], "correct": 1},
    {"difficulty": "medium", "question": "Trong trận Bạch Đằng năm 938, Ngô Quyền đã đánh bại quân xâm lược nào?", "answers": ["Quân Nam Hán", "Quân Tống", "Quân Nguyên Mông", "Quân Minh"], "correct": 0}
]

LOCAL_HARD_QUESTIONS = [
    {"difficulty": "hard", "question": "Nhạc sĩ Văn Cao sáng tác ca khúc Tiến quân ca (Quốc ca Việt Nam) vào năm nào?", "answers": ["1943", "1944", "1945", "1946"], "correct": 1},
    {"difficulty": "hard", "question": "Nhà nước phong kiến đầu tiên của Việt Nam thực hiện khoa thi tiến sĩ là triều đại nào?", "answers": ["Triều Lý", "Triều Trần", "Triều Lê Sơ", "Triều Nguyễn"], "correct": 0},
    {"difficulty": "hard", "question": "Hành tinh nào trong Hệ Mặt Trời có thời gian một ngày dài hơn một năm của chính nó?", "answers": ["Sao Thủy", "Sao Kim", "Sao Hỏa", "Sao Thổ"], "correct": 1},
    {"difficulty": "hard", "question": "Định lý toán học nổi tiếng Fermat lớn (Fermat's Last Theorem) được chứng minh hoàn toàn bởi ai vào năm 1994?", "answers": ["Alan Turing", "John Nash", "Andrew Wiles", "Grigori Perelman"], "correct": 2},
    {"difficulty": "hard", "question": "Ai là vị hoàng đế cuối cùng của triều đại nhà Trần trước khi Hồ Quý Ly lên ngôi?", "answers": ["Trần Thuận Tông", "Trần Thiếu Đế", "Trần Phế Đế", "Trần Nghệ Tông"], "correct": 1},
    {"difficulty": "hard", "question": "Nguyên tố hóa học Copernici (Cn, số hiệu nguyên tử 112) được đặt tên theo nhà bác học nào?", "answers": ["Albert Einstein", "Isaac Newton", "Nicolaus Copernicus", "Marie Curie"], "correct": 2},
    {"difficulty": "hard", "question": "Bộ luật thành văn đầu tiên của Việt Nam có tên là gì, được ban hành dưới thời vua Lý Thái Tông?", "answers": ["Quốc triều hình luật", "Hình thư", "Hoàng Việt luật lệ", "Luật Hồng Đức"], "correct": 1},
    {"difficulty": "hard", "question": "Ngọn núi cao nhất của châu Âu (nếu không tính vùng Kavkaz) là ngọn núi nào?", "answers": ["Mont Blanc", "Elbrus", "Matterhorn", "Olympus"], "correct": 0},
    {"difficulty": "hard", "question": "Eo biển hẹp nhất thế giới nối giữa biển Đen và biển Marmara có tên là gì?", "answers": ["Eo biển Gibraltar", "Eo biển Bosporus", "Eo biển Malacca", "Eo biển Bering"], "correct": 1},
    {"difficulty": "hard", "question": "Ai là người đầu tiên tìm ra cấu trúc chuỗi xoắn kép của DNA cùng với Francis Crick vào năm 1953?", "answers": ["Gregor Mendel", "James Watson", "Rosalind Franklin", "Louis Pasteur"], "correct": 1},
    {"difficulty": "hard", "question": "Tác phẩm văn học cổ điển 'Don Quixote' của nhà văn Tây Ban Nha Cervantes gồm có bao nhiêu phần?", "answers": ["1 phần", "2 phần", "3 phần", "4 phần"], "correct": 1},
    {"difficulty": "hard", "question": "Quốc gia nào có đường bờ biển dài nhất thế giới?", "answers": ["Nga", "Canada", "Úc", "Mỹ"], "correct": 1},
    {"difficulty": "hard", "question": "Ai là tác giả của tác phẩm quân sự cổ 'Binh thư yếu lược'?", "answers": ["Trần Hưng Đạo", "Trần Quang Khải", "Lê Lợi", "Nguyễn Trãi"], "correct": 0},
    {"difficulty": "hard", "question": "Giải Nobel Vật lý đầu tiên được trao cho ai vào năm 1901?", "answers": ["Albert Einstein", "Wilhelm Röntgen", "Marie Curie", "Max Planck"], "correct": 1},
    {"difficulty": "hard", "question": "Tỉnh nào ở Việt Nam có đường bờ biển dài nhất nước?", "answers": ["Khánh Hòa", "Quảng Ninh", "Cà Mau", "Bình Thuận"], "correct": 0}
]

def get_local_fallback_questions():
    """Lấy ngẫu nhiên 5 câu dễ (1-5), 5 câu trung bình (6-10), 5 câu khó (11-15) từ ngân hàng câu hỏi cục bộ và xáo trộn đáp án."""
    easy = random.sample(LOCAL_EASY_QUESTIONS, 5)
    medium = random.sample(LOCAL_MEDIUM_QUESTIONS, 5)
    hard = random.sample(LOCAL_HARD_QUESTIONS, 5)
    
    result = []
    # Trộn đáp án cho từng câu
    for q in easy:
        answers = list(q['answers'])
        correct_ans = answers[q['correct']]
        random.shuffle(answers)
        result.append({
            'difficulty': 'easy',
            'question': q['question'],
            'answers': answers,
            'correct': answers.index(correct_ans)
        })
    for q in medium:
        answers = list(q['answers'])
        correct_ans = answers[q['correct']]
        random.shuffle(answers)
        result.append({
            'difficulty': 'medium',
            'question': q['question'],
            'answers': answers,
            'correct': answers.index(correct_ans)
        })
    for q in hard:
        answers = list(q['answers'])
        correct_ans = answers[q['correct']]
        random.shuffle(answers)
        result.append({
            'difficulty': 'hard',
            'question': q['question'],
            'answers': answers,
            'correct': answers.index(correct_ans)
        })
    return result


used_question_ids = set()
