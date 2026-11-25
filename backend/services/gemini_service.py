"""
Tầng 2B — Google Gemini AI Service
===========================================================
File: backend/services/gemini_service.py
Mô tả: Khởi tạo duy nhất 1 Gemini Client từ Config, cung cấp 3 nghiệp vụ AI:
       1. Sinh 15 câu hỏi trắc nghiệm thuần Việt theo độ khó tăng dần.
       2. Chatbot MC trợ lý ảo (không lộ đáp án).
       3. Dịch câu hỏi & 4 đáp án sang ngôn ngữ mục tiêu.
"""

import json
from google import genai

from backend.config import Config

_gemini_client = None
_initialized = False


def get_gemini_client():
    """Khởi tạo lười (lazy singleton) 1 instance Gemini Client duy nhất."""
    global _gemini_client, _initialized
    if _initialized:
        return _gemini_client

    _initialized = True
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        print("⚠️ Cảnh báo: Không tìm thấy GEMINI_API_KEY")
        _gemini_client = None
        return None

    try:
        _gemini_client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"⚠️ Lỗi khởi tạo Gemini client: {e}")
        _gemini_client = None

    return _gemini_client


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _is_valid_question_list(items) -> bool:
    if not isinstance(items, list) or len(items) < 15:
        return False
    for q in items[:15]:
        if not isinstance(q, dict):
            return False
        if not isinstance(q.get("question"), str) or not q["question"].strip():
            return False
        answers = q.get("answers")
        if not isinstance(answers, list) or len(answers) != 4:
            return False
        correct = q.get("correct")
        if not isinstance(correct, int) or not (0 <= correct <= 3):
            return False
    return True


def generate_questions_with_ai():
    """Dùng Gemini AI để tạo ra bộ 15 câu hỏi mới theo độ khó tăng dần."""
    client = get_gemini_client()
    if not client:
        return None

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
        response = client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=prompt,
        )
        res_text = "".join(
            part.text for part in response.candidates[0].content.parts if part.text
        ).strip()

        start_idx = res_text.find("[")
        end_idx = res_text.rfind("]")
        if start_idx != -1 and end_idx != -1:
            res_text = res_text[start_idx : end_idx + 1]

        parsed = json.loads(res_text)
        if _is_valid_question_list(parsed):
            return parsed[:15]
    except Exception as e:
        print(f"⚠️ Lỗi từ AI trong việc sinh câu hỏi: {e}")

    return None


def generate_mc_reply(player_name: str, current_question: int, message: str) -> str:
    """Sinh phản hồi đóng vai MC Trợ Lý ảo (không tiết lộ đáp án đúng)."""
    client = get_gemini_client()
    if not client:
        return (
            "⚠️ Lỗi: Chưa cấu hình GEMINI_API_KEY trong file .env hoặc hệ thống "
            "nên chatbot đang bị vô hiệu hóa."
        )

    prompt = f'''Bạn là MC Trợ Lý ảo của trò chơi "Ai Là Triệu Phú".
Tên người chơi là: {player_name}. Người chơi đang ở câu hỏi số {current_question + 1}/15.
Luật trò chơi: Có 15 câu hỏi, 3 quyền trợ giúp (50:50, Gọi ĐT, Hỏi khán giả), 2 mốc an toàn ở câu 5 và câu 10.

Câu hỏi/tin nhắn của người chơi: "{message}"

Nhiệm vụ: Trả lời người chơi bằng giọng điệu vui vẻ, tự nhiên, thân thiện và động viên họ.
QUAN TRỌNG: KHÔNG ĐƯỢC để lộ đáp án đúng của bất kỳ câu hỏi nào nếu họ yêu cầu gợi ý (hãy khuyên họ dùng quyền trợ giúp).
Hãy trả lời ngắn gọn, súc tích (dưới 3 câu).'''

    try:
        response = client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"⚠️ Lỗi Gemini chatbot: {e}")
        return "Xin lỗi, tôi đang gặp trục trặc hệ thống. Vui lòng thử lại!"


def translate_question_with_ai(question_text: str, answers: list[str], target_lang: str) -> dict:
    """Dịch câu hỏi và 4 phương án sang target_lang bằng Gemini AI."""
    client = get_gemini_client()
    if not client:
        raise RuntimeError("Chưa cấu hình GEMINI_API_KEY")

    ans_texts = ", ".join(f"{chr(65 + i)}: {ans}" for i, ans in enumerate(answers))
    prompt = f'''Dịch câu hỏi trắc nghiệm dưới đây sang {target_lang}.
Câu hỏi: {question_text}
Các đáp án: {ans_texts}
Trả về kết quả 100% dưới dạng chuỗi JSON nguyên gốc, KHÔNG BỌC trong markdown (chỉ format: {{"question": "câu hỏi đã dịch", "answers": ["dịch A", "dịch B", "dịch C", "dịch D"]}}), không thêm bất kỳ chữ nào khác.'''

    response = client.models.generate_content(
        model=Config.GEMINI_MODEL,
        contents=prompt,
    )
    res_text = _strip_markdown_fences(response.text)
    translated_data = json.loads(res_text)
    if not isinstance(translated_data, dict) or "question" not in translated_data or "answers" not in translated_data:
        raise ValueError("Phản hồi dịch từ AI không đúng định dạng JSON mong đợi")
    return translated_data
