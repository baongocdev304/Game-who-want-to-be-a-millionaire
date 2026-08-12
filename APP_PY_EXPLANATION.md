# 🧠 GIẢI THÍCH CHI TIẾT MÃ NGUỒN `app.py` — HỆ THỐNG BACKEND SERVER

File [app.py](file:///Users/nguyenbaongoc/Documents/millionaire/app.py) là **"trung tâm điều khiển"** của toàn bộ game Ai Là Triệu Phú. Server này xử lý từ việc kết nối AI, phân bổ câu hỏi, quản lý tài khoản, gửi email khôi phục mật khẩu, đến cổng thanh toán tự động Sepay Webhook.

Dưới đây là tài liệu mổ xẻ chi tiết từng dòng lệnh và luồng logic trong file để bạn học tập.

---

## 🗺️ TỔNG QUAN PHÂN CHIA PHẦN CỨNG & PHẦN MỀM CỦA `app.py`

Mã nguồn của `app.py` được chia làm 6 khối chính:
1. **Khối 1:** Import thư viện & Cấu hình ban đầu (AI Client, SMTP Mail, CORS, Flask App).
2. **Khối 2:** Các tiện ích cơ sở dữ liệu (Database Helpers, Session, Bcrypt).
3. **Khối 3:** Hệ thống Authentication (Đăng ký, Đăng nhập, Khôi phục mật khẩu qua Email).
4. **Khối 4:** Logic Game & AI (AI Sinh câu hỏi, Kiểm tra đáp án, Quyền trợ giúp, Timeout).
5. **Khối 5:** Chatbot MC Trợ lý ảo & Dịch thuật (MC Chatbot, Translate MC).
6. **Khối 6:** Hệ thống Cửa hàng & Sepay Webhook nạp lượt chơi tự động.

---

## 1. 📦 KHAI BÁO THƯ VIỆN & CẤU HÌNH BAN ĐẦU

### A. Giải thích cú pháp Import
```python
import os                       # Đọc biến môi trường (.env) và tệp hệ thống
import json                     # Làm việc với dữ liệu JSON (parse/stringify)
import random                   # Sinh mã số ngẫu nhiên, trộn câu hỏi
import uuid                     # Tạo chuỗi định danh duy nhất (UUID) cho phiên chơi
import time                     # Theo dõi thời gian chơi của người dùng
import smtplib                  # Thư viện chuẩn để gửi email qua giao thức SMTP
import bcrypt                   # Mã hóa mật khẩu
import psycopg2                 # Driver kết nối PostgreSQL
import psycopg2.extras          # Cung cấp DictCursor (truy vấn trả về dạng Dictionary)
from functools import wraps     # Giúp viết Decorator không bị trùng tên hàm
from flask import Flask, jsonify, request, render_template, session, redirect, g
from flask_cors import CORS     # Xử lý lỗi bảo mật chia sẻ tài nguyên đa domain
from dotenv import load_dotenv  # Tải tệp cấu hình .env
from google import genai        # SDK Gemini AI thế hệ mới
```

### B. Khởi tạo Gemini Client
```python
load_dotenv() # Tải các cặp KEY=VALUE trong .env vào biến môi trường hệ thống

try:
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        gemini_client = genai.Client(api_key=api_key) # Khởi tạo kết nối Google API
    else:
        gemini_client = None
except Exception as e:
    gemini_client = None
```
*   **Cú pháp cần học:** `os.environ.get('KEY')` giúp lấy giá trị cấu hình một cách an toàn mà không làm sập chương trình nếu KEY đó chưa được định nghĩa (nó sẽ trả về `None`).

### C. Khởi tạo Web Server Flask & CORS
```python
app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

# Cấu hình chuỗi khóa bí mật dùng để mã hóa Cookie Session ở trình duyệt
app.secret_key = os.environ.get('SECRET_KEY', 'millionaire-secret-2026-xK9mP')

# Cho phép gọi API xuyên cổng (ví dụ: client chạy cổng 5500 gọi vào API server cổng 5001)
CORS(app, supports_credentials=True)
```
*   `__name__`: Biến đặc biệt của Python cho biết file này đang được chạy trực tiếp hay được import dưới dạng một module.
*   `supports_credentials=True`: Cho phép trình duyệt gửi kèm Cookies/Session trong các request API không cùng domain.

---

## 2. 🗄️ TIỆN ÍCH CƠ SỞ DỮ LIỆU & DECORATORS

### A. Quản lý vòng đời kết nối PostgreSQL thông qua biến cục bộ `g`
Để tránh lãng phí kết nối, Flask cung cấp biến toàn cục của luồng request tên là `g`.
```python
def get_db():
    if 'db' not in g:
        g.db = get_connection() # Lấy một kết nối từ bể Connection Pool
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        release_connection(db) # Trả kết nối về bể chứa khi xử lý xong request
```
*   `@app.teardown_appcontext`: Decorator đặc biệt của Flask tự động chạy khi kết thúc một HTTP request. Việc này đảm bảo kết nối Database **luôn luôn được giải phóng** ngay cả khi code bị crash hoặc sinh lỗi 500.

### B. Làm việc với `DictCursor` trong psycopg2
Mặc định, truy vấn SQL trả về một tuple (ví dụ: `('player01', 'email@gmail.com')`), ta phải lấy theo index `row[0]`, rất dễ nhầm lẫn. `DictCursor` giúp trả về dạng Dictionary.
```python
# Cách thiết lập trong code:
conn = get_db()
with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
    cur.execute("SELECT username, email FROM users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    # Bạn có thể học cách truy xuất trực tiếp bằng tên cột:
    email = row['email'] 
```

### C. Decorator `@login_required` (Gác cổng bảo mật)
```python
def login_required(f):
    @wraps(f) # Giữ nguyên tên gốc của hàm f, ngăn lỗi trùng lặp route của Flask
    def decorated(*args, **kwargs):
        if 'username' not in session:
            # Nếu chưa đăng nhập, trả về trang Auth để họ đăng nhập
            return redirect('/auth')
        return f(*args, **kwargs) # Nếu đã đăng nhập, cho phép chạy tiếp hàm f
    return decorated
```
*   **Cách hoạt động:** Khi bạn đặt `@login_required` phía trên một hàm route, hàm gác cổng này sẽ được chạy trước. Nếu nó trả về `redirect('/auth')`, luồng xử lý bị cắt và trình duyệt chuyển hướng ngay.

---

## 3. 🔐 HỆ THỐNG AUTHENTICATION & ĐẶT LẠI MẬT KHẨU

### A. Endpoint Đăng Ký (`/api/auth/register`)
Khi người dùng điền Form và gửi dữ liệu POST:
1. Đọc dữ liệu JSON: `data = request.get_json()`.
2. Kiểm tra tài khoản/email đã tồn tại trong CSDL chưa bằng lệnh SQL:
   `SELECT user_id FROM users WHERE username = %s OR email = %s`
3. Nếu chưa tồn tại, mã hóa mật khẩu và tạo bản ghi đồng thời trong 3 bảng: `users`, `user_passwords`, `rankings` và `user_wallets` (mỗi tài khoản đăng ký mới được tặng sẵn 3 lượt chơi miễn phí).

#### ⚠️ Sử dụng SQL Transaction với Rollback để đảm bảo tính toàn vẹn (ACID):
```python
conn = get_db()
try:
    with conn.cursor() as cur:
        # Bước 1: Thêm user mới
        cur.execute("INSERT INTO users ... RETURNING user_id")
        user_id = cur.fetchone()[0]

        # Bước 2: Thêm hash mật khẩu
        cur.execute("INSERT INTO user_passwords ...")

        # Bước 3: Khởi tạo ví tiền & xếp hạng
        cur.execute("INSERT INTO user_wallets ...")
        cur.execute("INSERT INTO rankings ...")

    # Xác nhận tất cả các lệnh INSERT trên thành công đồng thời
    conn.commit()
except Exception as e:
    # Nếu bất kỳ bảng nào lỗi (ví dụ: mất kết nối ở bước 3), hoàn tác toàn bộ!
    conn.rollback() 
    return jsonify({"success": False, "error": "Lỗi hệ thống"}), 500
```

### B. Endpoint Quên Mật Khẩu (`/api/auth/forgot-password`)
Luồng hoạt động:
1. Người dùng nhập Email -> Hệ thống kiểm tra xem email đó có thuộc tài khoản nào không.
2. Sinh mã xác thực ngẫu nhiên 6 chữ số: `reset_code = f"{random.randint(100000, 999999)}"`
3. Thiết lập thời gian hết hạn là 15 phút: `expires_at = datetime.now() + timedelta(minutes=15)`
4. Lưu mã này vào bảng `password_reset_codes`.
5. Gọi hàm gửi email `send_email_code(email, reset_code)`. Nếu hệ thống chưa cấu hình SMTP trong `.env`, code sẽ in mã này ra terminal để lập trình viên có thể copy và test.

---

## 4. 🎮 LOGIC GAME & TÍCH HỢP GEMINI AI

### A. Sinh 15 câu hỏi tự động qua AI (`generate_questions_with_ai`)
Hàm này gửi một Prompt được thiết kế tinh xảo đến Gemini AI yêu cầu trả về cấu trúc mảng JSON 15 câu hỏi phân bổ: 5 câu dễ, 5 câu trung bình, 5 câu khó.

#### 💡 Cơ chế bắt buộc Gemini trả về JSON thuần:
Mô hình AI thường có thói quen trả về thêm các thẻ markdown như ` ```json ` hay các lời dẫn mở đầu. Điều này sẽ làm hỏng hàm parse `json.loads()`.
```python
# Cách giải quyết trong app.py:
res_text = response.text.strip()

# Loại bỏ các ký tự Markdown bao bọc nếu AI lỡ sinh ra
if res_text.startswith("```"):
    # Tách dòng đầu và cuối
    lines = res_text.splitlines()
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines[-1].startswith("```"):
        lines = lines[:-1]
    res_text = "\n".join(lines).strip()
```

### B. Endpoint Bắt Đầu Chơi (`/api/game/start`)
Khi nhận request POST từ client:
1. Trừ 1 lượt chơi của user trong bảng `user_wallets`. Nếu `game_turns <= 0`, từ chối cho chơi và yêu cầu nạp thêm lượt.
2. Gọi hàm sinh câu hỏi AI. Nếu lỗi hoặc hết giới hạn API Key của Google, tự động nạp bộ câu hỏi dự phòng lưu trong file cục bộ:
   ```python
   questions = generate_questions_with_ai()
   if not questions:
       questions = load_local_fallback_questions() # Luôn có phương án dự phòng!
   ```
3. Khởi tạo một mã phiên chơi duy nhất (`session_id = str(uuid.uuid4())`).
4. Lưu trạng thái game (Danh sách 15 câu hỏi, chỉ mục câu hiện tại `current_question = 0`, thời gian bắt đầu) vào một Dictionary lưu trữ trong bộ nhớ tạm thời `GAME_SESSIONS` của server.
5. Chỉ gửi câu hỏi số 1 (không gửi đáp án đúng) về cho client để chống hack:
   ```python
   return jsonify({
       "success": True,
       "session_id": session_id,
       "question_number": 1,
       "question": {
           "question": questions[0]["question"],
           "answers": questions[0]["answers"]
       }
   })
   ```

### C. Endpoint Trả Lời Câu Hỏi (`/api/game/answer`)
Trình duyệt gửi lên `session_id` và số chỉ mục đáp án người chơi chọn (`selected_answer` từ 0 đến 3).
1. Server tìm lại thông tin phiên chơi trong bộ nhớ `GAME_SESSIONS`.
2. So sánh lựa chọn với đáp án đúng:
   ```python
   is_correct = (selected_answer == correct_answer)
   ```
3. **Nếu Đúng:**
   * Tăng chỉ mục câu hỏi lên 1.
   * Nếu đã vượt qua câu 15 -> Trận đấu kết thúc ở trạng thái **Thắng Cuộc** (`win`).
   * Cộng tiền thưởng tương ứng. Gửi câu hỏi tiếp theo về cho người chơi.
4. **Nếu Sai:**
   * Game kết thúc ngay lập tức ở trạng thái **Thất Bại** (`loss`).
   * Tính toán tiền thưởng dựa trên **Mốc An Toàn** gần nhất mà người chơi đã vượt qua (Câu 5 hoặc Câu 10). Nếu chưa qua câu 5, tiền thưởng trở về `0 đ`.
   * Ghi lịch sử trận đấu vào bảng `game_history` và cập nhật bảng `rankings` (+1 thua).

### D. Endpoint Quyền Trợ Giúp (`/api/game/lifeline`)
Xử lý 3 quyền trợ giúp kinh điển:
*   **50/50:** Tìm ra 2 đáp án sai trong số 3 đáp án sai hiện tại và gửi về chỉ mục của chúng để Client ẩn đi.
*   **Khán giả (Audience Poll):** Sinh ngẫu nhiên tỷ lệ phần trăm bình chọn sao cho đáp án đúng luôn chiếm tỷ lệ cao nhất (phù hợp với thực tế gameshow).
*   **Gọi điện người thân (Call Friend):** Sử dụng Gemini AI để giả lập tính cách của người thân và đưa ra câu thoại gợi ý:
    ```python
    prompt = f"Hãy đóng vai là người thân của người chơi... đưa ra gợi ý cho câu hỏi: '{q['question']}'..."
    # Gọi AI trả về câu thoại tự nhiên
    ```

---

## 5. 🤖 MC TRỢ LÝ ẢO & DỊCH THUẬT

### A. MC Chatbot (`/api/chatbot`)
Góc màn hình có MC Trợ lý nói chuyện.
*   Để MC nói chuyện thông minh, server gửi kèm lịch sử chơi game của phiên hiện tại vào prompt của AI (đang ở câu số mấy, tiền thưởng bao nhiêu).
*   AI sẽ bình luận chính xác về tiến độ chơi của bạn (ví dụ: "Cố lên, bạn đã qua câu 10 rồi đó!").

### B. MC Thay đổi tính cách (`/api/translate`)
*   Người chơi có thể chọn MC nói giọng standard (lịch sự), street (đường phố, giang hồ), hoặc GenZ (nhiều teencode, hài hước).
*   Hệ thống dùng Gemini AI dịch câu thoại gốc của MC sang phong cách được chọn trước khi hiển thị.

---

## 6. 💳 CỬA HÀNG & SEPAY WEBHOOK

Hệ thống nạp tiền tự động là điểm nhấn kỹ thuật quan trọng của dự án.

### A. Tạo Đơn Hàng (`/api/shop/create-order`)
Khi người dùng chọn mua lượt:
1. Tạo mã thanh toán duy nhất: `payment_ref = f"ALTP{int(time.time())}"`
2. Lưu bản ghi vào bảng `shop_transactions` ở trạng thái `pending`.
3. Sinh link QR VietQR tự động để hiển thị ở frontend:
   `https://img.vietqr.io/image/{bank_code}-{account_no}-compact2.png?amount={amount}&addInfo={payment_ref}`
   *   *Ý nghĩa:* Khi người dùng quét mã này bằng ứng dụng ngân hàng, số tiền và nội dung chuyển khoản (`addInfo`) sẽ tự động được điền chính xác, tránh việc người dùng gõ sai mã `payment_ref`.

### B. Sepay Webhook (`/api/shop/webhook`)
Khi có biến động số dư thực tế, Sepay gửi một POST request chứa thông tin giao dịch.
```python
# 1. Xác thực xuất xứ tin nhắn
sepay_key = request.headers.get('x-sepay-secret-key')
if sepay_key != WEBHOOK_SECRET:
    return jsonify({"success": False, "error": "Unauthorized"}), 401

# 2. Tìm kiếm mã hóa đơn trong nội dung chuyển khoản
payload = request.get_json()
transaction_content = payload.get('transaction_content', '')
# Tìm chuỗi ALTPxxxxx bằng biểu thức chính quy (Regex)
match = re.search(r'ALTP\d+', transaction_content)
```

#### 🔒 Sử dụng `SAVEPOINT` để hỗ trợ hệ thống cũ:
Khi nâng cấp cấu trúc database, bảng `users` cũ có thể có cột `plays_left` hoặc không. Để tránh việc câu lệnh lỗi làm hỏng cả tiến trình giao dịch đang chạy, hệ thống sử dụng điểm khôi phục cục bộ (`SAVEPOINT`).
```python
try:
    cur.execute("SAVEPOINT legacy_update")
    cur.execute("UPDATE users SET plays_left = ...") # Thao tác có thể lỗi
    cur.execute("RELEASE SAVEPOINT legacy_update")   # Thành công thì giải phóng điểm khôi phục
except Exception as e:
    cur.execute("ROLLBACK TO SAVEPOINT legacy_update") # Nếu lỗi, chỉ hủy lệnh UPDATE trên
    # Giao dịch nạp tiền chính vẫn được ghi nhận thành công!
```

---

## 🚀 ĐỀ XUẤT THỰC HÀNH TỰ HỌC TRÊN FILE `app.py`

Để làm chủ kiến thức trong `app.py`, bạn hãy thử thực hành các bài tập sau:

1.  **Chỉnh sửa Mốc An Toàn:**
    Tìm danh sách `MILESTONES = [4, 9]` (tương ứng với câu 5 và câu 10). Thử sửa thành `MILESTONES = [2, 7, 11]` để tạo ra 3 mốc an toàn mới tại câu 3, câu 8 và câu 12. Chạy lại game và xem sự thay đổi của tiền thưởng khi trả lời sai.
2.  **Tùy biến Prompt của Gemini AI:**
    Tìm đoạn định nghĩa `prompt` trong hàm `generate_questions_with_ai`. Sửa prompt để yêu cầu AI **chỉ tạo câu hỏi về lĩnh vực thể thao** hoặc **chỉ tạo câu hỏi bằng tiếng Anh** để học cách điều khiển AI.
3.  **Tự tạo một Route API đơn giản:**
    Thêm đoạn code sau vào cuối file `app.py` để tự tạo một đường dẫn kiểm tra trạng thái nhanh:
    ```python
    @app.route('/api/ping')
    def ping():
        return jsonify({"message": "pong", "time": time.time()})
    ```
    Mở trình duyệt truy cập `http://localhost:5001/api/ping` để kiểm tra kết quả!
