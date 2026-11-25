"""
Tầng 2B — Offline Question Bank Service
===========================================================
File: backend/services/question_bank.py
Mô tả: Nguồn duy nhất lưu 45 câu hỏi dự phòng thuần Việt (15 dễ, 15 trung bình, 15 khó)
       và hàm bốc ngẫu nhiên + xáo trộn phương án khi Gemini AI không khả dụng.
"""

import random

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
    {"difficulty": "easy", "question": "Loài chim nào thường báo hiệu mùa xuân về ở Việt Nam?", "answers": ["Chim sẻ", "Chim én", "Chim bồ câu", "Chim họa mi"], "correct": 1},
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
    {"difficulty": "medium", "question": "Trong trận Bạch Đằng năm 938, Ngô Quyền đã đánh bại quân xâm lược nào?", "answers": ["Quân Nam Hán", "Quân Tống", "Quân Nguyên Mông", "Quân Minh"], "correct": 0},
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
    {"difficulty": "hard", "question": "Tỉnh nào ở Việt Nam có đường bờ biển dài nhất nước?", "answers": ["Khánh Hòa", "Quảng Ninh", "Cà Mau", "Bình Thuận"], "correct": 0},
]


def _shuffle_question(q: dict, difficulty: str) -> dict:
    answers = list(q["answers"])
    correct_ans = answers[q["correct"]]
    random.shuffle(answers)
    return {
        "difficulty": difficulty,
        "question": q["question"],
        "answers": answers,
        "correct": answers.index(correct_ans),
    }


def get_local_fallback_questions() -> list[dict]:
    """Bốc ngẫu nhiên 5 câu dễ, 5 câu trung bình, 5 câu khó và xáo trộn vị trí 4 đáp án."""
    easy = random.sample(LOCAL_EASY_QUESTIONS, 5)
    medium = random.sample(LOCAL_MEDIUM_QUESTIONS, 5)
    hard = random.sample(LOCAL_HARD_QUESTIONS, 5)

    result = []
    for q in easy:
        result.append(_shuffle_question(q, "easy"))
    for q in medium:
        result.append(_shuffle_question(q, "medium"))
    for q in hard:
        result.append(_shuffle_question(q, "hard"))
    return result
