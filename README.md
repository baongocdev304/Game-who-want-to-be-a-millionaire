# 🎯 Ai Là Triệu Phú — Who Wants To Be A Millionaire

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Gemini_AI-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini AI">
  <img src="https://img.shields.io/badge/PWA-5A0FC8?style=for-the-badge&logo=pwa&logoColor=white" alt="PWA">
</p>

**Ai Là Triệu Phú** là một trò chơi trực tuyến lấy cảm hứng từ gameshow truyền hình nổi tiếng *Who Wants To Be A Millionaire*, được xây dựng hoàn toàn bằng tiếng Việt. Game sử dụng **Gemini AI** để tự động sinh câu hỏi theo độ khó tăng dần, có hệ thống tài khoản, cửa hàng mua lượt chơi, tích hợp thanh toán qua **SePay**, và hỗ trợ cài đặt dưới dạng **Progressive Web App (PWA)** trên điện thoại.

---

## 📸 Tính năng nổi bật

### 🎮 Gameplay
- **15 câu hỏi** với độ khó tăng dần từ Dễ → Trung bình → Khó, tương ứng 3 mức: Câu 1-5, 6-10, 11-15
- **15 mức tiền thưởng** từ 200.000 đ đến 150.000.000 đ (150 triệu)
- **2 mốc an toàn** tại câu 5 (2.000.000 đ) và câu 10 (22.000.000 đ) — trả lời sai vẫn giữ được tiền mốc an toàn
- **3 quyền trợ giúp**: 50:50 (loại 2 đáp án sai), Gọi điện (70% chính xác), Hỏi khán giả (biểu đồ bình chọn)
- **Đồng hồ đếm ngược 30 giây** cho mỗi câu hỏi
- **Dừng cuộc chơi** bất kỳ lúc nào để mang về tiền thưởng hiện tại

### 🤖 AI Tích hợp (Gemini)
- **Sinh câu hỏi tự động** bằng Gemini Flash AI — mỗi ván chơi có bộ câu hỏi hoàn toàn mới
- **Chatbot MC Trợ Lý** — trả lời câu hỏi về luật chơi, chiến lược, động viên người chơi, không bao giờ lộ đáp án
- **Dịch câu hỏi** sang ngôn ngữ khác (English, v.v.) nhờ AI
- **Bộ câu hỏi dự phòng offline** — 45 câu hỏi thuần Việt được chuẩn bị sẵn (15 easy + 15 medium + 15 hard) trong trường hợp mất mạng

### 👤 Hệ thống tài khoản
- Đăng ký / Đăng nhập bằng Username + Mật khẩu (mã hóa bcrypt)
- **Quên mật khẩu** — gửi mã xác nhận 6 số qua Email, hết hạn sau 15 phút
- Phiên đăng nhập quản lý bằng Flask Session

### 🛒 Cửa hàng & Thanh toán
- **Ví người chơi**: Lượt chơi miễn phí (3 lượt ban đầu) và Lượt trợ giúp dự phòng
- **Cửa hàng mua vật phẩm**: Lượt chơi (5.000 đ/lượt) và Trợ giúp dự phòng (2.000 đ/lượt)
- **Tích hợp thanh toán SePay**: Tạo mã QR VietQR tự động, nhận webhook xác nhận thanh toán
- **Hệ thống webhook bảo mật**: Xác thực HMAC-SHA256 qua nhiều phương thức (X-SePay-Signature, Authorization, X-API-Key)

### 🏆 Bảng xếp hạng & Lịch sử
- **Bảng xếp hạng Top 10** dựa trên tổng điểm từ PostgreSQL
- **Lịch sử chơi** — lưu trữ kết quả từng ván (thắng/thua, điểm số, thời gian chơi)
- Tự động cập nhật win_rate qua database trigger

### 📱 Progressive Web App (PWA)
- Cài đặt lên màn hình chính điện thoại (iPhone/Android)
- Hoạt động như ứng dụng native với màn hình splash, icon riêng
- Giao diện responsive — tối ưu cho cả desktop lẫn mobile

### ✨ Giao diện
- Thiết kế **Maximalism / Dopamine** với hiệu ứng Cosmic Space, sao bay, pháo giấy
- Gradient text động, hiệu ứng glow, shadow-hard, particle animation
- Âm thanh tương tác bằng Web Audio API (chọn đáp án, đúng, sai, trợ giúp)
- Hỗ trợ chế độ **Reduced Motion** cho accessibility

---

## 🏗️ Kiến trúc dự án

```
Game-who-want-to-be-a-millionaire/
├── app.py                  # Backend Flask chính — toàn bộ API endpoints
├── database.py             # Kết nối PostgreSQL, tạo schema, trigger, sample data
├── update_db.py            # Script cập nhật thêm bảng transactions
├── requirements.txt        # Thư viện Python cần cài
├── start.sh                # Script khởi động (Flask + ngrok cho webhook)
├── .gitignore
│
├── templates/
│   ├── index.html          # Trang chủ game (Welcome, Game, Result, Shop screens)
│   ├── auth.html           # Trang đăng nhập / đăng ký / quên mật khẩu
│   └── shop.html           # Trang cửa hàng mua vật phẩm
│
├── static/
│   ├── css/
│   │   └── style.css       # Design system (tokens, animations, responsive)
│   ├── js/
│   │   └── game.js         # Frontend logic — gọi API, xử lý UI, chatbot, âm thanh
│   ├── icons/
│   │   ├── icon-192.png    # PWA icon 192x192
│   │   └── icon-512.png    # PWA icon 512x512
│   ├── manifest.json       # PWA manifest
│   └── sw.js               # Service Worker (xóa cache, fetch trực tiếp)
│
└── scratch/                # Scripts test & debug
    ├── create_db.py
    ├── check_db_columns.py
    ├── list_models.py
    ├── test_apis.py
    ├── test_fallback.py
    ├── test_final.py
    ├── test_flash_latest.py
    └── test_webhook.py
>>>>>>> origin/main
```

---

<<<<<<< HEAD
## 1. 📦 CẤU HÌNH THƯ VIỆN & BIẾN MÔI TRƯỜNG

### File 1: `requirements.txt`
*   **Mục đích:** Khai báo toàn bộ các thư viện Python (dependencies) cần thiết để chạy dự án. Khi di chuyển dự án sang máy tính khác, bạn chỉ cần chạy 1 lệnh để cài lại tất cả.
*   **Chi tiết câu lệnh để học:**
    ```text
    Flask==3.0.2
    Flask-CORS==4.0.0
    google-genai==0.1.1
    python-dotenv==1.0.1
    psycopg2-binary==2.9.9
    bcrypt==4.1.2
    ```
*   **Giải thích từng thư viện:**
    *   `Flask`: Framework giúp dựng Web Server gọn nhẹ, tạo các đường dẫn (routes) và API.
    *   `Flask-CORS`: Xử lý lỗi bảo mật CORS (Cross-Origin Resource Sharing), cho phép Frontend ở domain/cổng khác gọi vào API của Backend.
    *   `google-genai`: Thư viện SDK chính thức của Google để kết nối và gửi câu hỏi (prompts) đến mô hình ngôn ngữ lớn Gemini.
    *   `python-dotenv`: Đọc các biến cấu hình từ file ẩn `.env` và đưa vào môi trường của hệ thống (thông qua `os.environ`).
    *   `psycopg2-binary`: Thư viện driver trung gian giúp Python có thể "nói chuyện" và gửi lệnh SQL tới hệ quản trị cơ sở dữ liệu PostgreSQL.
    *   `bcrypt`: Thư viện dùng để mã hóa một chiều (hashing) mật khẩu người dùng trước khi lưu vào CSDL để đảm bảo an toàn tuyệt đối.
*   **Lệnh cần chạy để học:**
    ```bash
    pip3 install -r requirements.txt
    ```
    *(Ý nghĩa: Trình quản lý thư viện Python `pip3` sẽ đọc file `requirements.txt` và cài đặt các phiên bản tương thích).*

---

### File 2: `.env` (Environment Variables)
*   **Mục đích:** Lưu trữ các cấu hình nhạy cảm (API Key, Mật khẩu Database, Tài khoản Webhook). File này **không bao giờ** được đưa lên Github công khai để tránh bị lộ mật mã.
*   **Chi tiết nội dung cần học:**
    ```ini
    DATABASE_URL=postgresql://postgres:123456@localhost:5432/millionaire
    GEMINI_API_KEY=AIzaSy...
    WEBHOOK_SECRET=your-secure-webhook-token
    ```
*   **Giải thích các biến quan trọng:**
    *   `DATABASE_URL`: Đường dẫn kết nối CSDL PostgreSQL theo định dạng chuẩn: `postgresql://[user]:[password]@[host]:[port]/[db_name]`.
    *   `GEMINI_API_KEY`: Khóa bảo mật do Google cấp để sử dụng dịch vụ Gemini AI.
    *   `WEBHOOK_SECRET`: Chuỗi khóa bí mật tự đặt để kiểm tra xem request nạp tiền gửi đến hệ thống của bạn có thực sự xuất phát từ Sepay hay không.

---

## 2. 🗄️ DATABASE & KHO LƯU TRỮ (POSTGRESQL & SQL)

### File 3: [database.py](file:///Users/nguyenbaongoc/Documents/millionaire/database.py)
*   **Mục đích:** Quản lý kết nối tới cơ sở dữ liệu PostgreSQL bằng kỹ thuật **Connection Pool** và chứa mã SQL để dựng toàn bộ cấu trúc bảng (Schema), Indexes và Trigger.

#### A. Kỹ thuật "Threaded Connection Pool" (Bể kết nối)
*   **Tại sao cần dùng?** Nếu mỗi lần có người dùng đăng nhập hay lấy câu hỏi, server lại tạo một kết nối mới tới database và đóng lại ngay, hệ thống sẽ rất chậm do tốn thời gian thiết lập bắt tay (handshake). Connection Pool tạo sẵn một nhóm kết nối (từ 1 đến 20) và giữ nguyên chúng. Khi cần, Flask lấy ra dùng rồi trả lại ngay cho "bể chứa".
*   **Giải thích dòng code quan trọng:**
    ```python
    db_pool = psycopg2.pool.ThreadedConnectionPool(minconn=1, maxconn=20, dsn=db_url)
    ```
    *   `minconn=1`: Luôn giữ tối thiểu 1 kết nối hoạt động.
    *   `maxconn=20`: Cho phép mở tối đa 20 kết nối đồng thời trong môi trường đa luồng.
    *   `db_pool.getconn()`: Lấy một kết nối rảnh rỗi từ pool.
    *   `db_pool.putconn(conn)`: Trả kết nối đó về pool để người khác sử dụng.

#### B. Cấu trúc Schema SQL chính
*   **Khóa ngoại (FOREIGN KEY) với `ON DELETE CASCADE`:**
    ```sql
    CREATE TABLE IF NOT EXISTS user_passwords (
        user_id INT UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        ...
    );
    ```
    *   `REFERENCES users(user_id)`: Ràng buộc bảng mật khẩu phải liên kết chính xác với bảng người dùng.
    *   `ON DELETE CASCADE`: Khi một user bị xóa khỏi bảng `users`, toàn bộ mật khẩu liên kết của họ trong bảng `user_passwords` cũng tự động bị xóa theo, tránh để lại dữ liệu rác.

#### C. Database Trigger và Hàm PL/pgSQL
*   **Mục đích:** Tự động tính toán tỉ lệ thắng (`win_rate`) trực tiếp bên trong Database mỗi khi cập nhật điểm hoặc số trận đấu của người chơi, giải phóng tính toán cho backend Python.
*   **Giải thích dòng code quan trọng:**
    ```sql
    CREATE OR REPLACE FUNCTION update_win_rate()
    RETURNS TRIGGER AS $$
    BEGIN
        IF (NEW.total_wins + NEW.total_losses + NEW.total_draws) > 0 THEN
            NEW.win_rate := ROUND(
                NEW.total_wins::NUMERIC /
                (NEW.total_wins + NEW.total_losses + NEW.total_draws) * 100, 2
            );
        END IF;
        NEW.updated_at := CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    ```
    *   `NEW`: Từ khóa đặc biệt đại diện cho dòng dữ liệu mới chuẩn bị được cập nhật vào bảng.
    *   `NEW.total_wins::NUMERIC`: Ép kiểu số nguyên sang số thực (Numeric) để thực hiện phép chia có phần thập phân, tránh bị làm tròn thành `0`.
    *   `BEFORE UPDATE ON rankings`: Ràng buộc chạy hàm này **trước** khi dữ liệu thực sự được ghi xuống ổ đĩa, đảm bảo tỉ lệ thắng luôn chính xác.

---

### File 4: [update_db.py](file:///Users/nguyenbaongoc/Documents/millionaire/update_db.py)
*   **Mục đích:** File chạy tay phụ trợ để cập nhật cấu trúc database (thêm bảng giao dịch giao dịch `transactions` hoặc chỉnh sửa cột).
*   **Chi tiết câu lệnh để học:**
    ```python
    conn = psycopg2.connect(db_url)
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS...")
    conn.commit()
    ```
    *   `conn.cursor()`: Tạo ra một đối tượng "con trỏ" (cursor) để gửi các câu lệnh SQL vào CSDL.
    *   `with conn.cursor() as cur`: Đảm bảo con trỏ sẽ tự động đóng lại khi thực thi xong khối lệnh, tránh rò rỉ bộ nhớ.
    *   `conn.commit()`: **Cực kỳ quan trọng!** Xác nhận ghi tất cả các thay đổi vào CSDL. Nếu không gọi `commit()`, mọi thao tác ghi/sửa sẽ bị hủy bỏ (rollback) khi ngắt kết nối.
*   **Lệnh chạy kiểm tra:**
    ```bash
    python3 update_db.py
    ```

---

## 3. 🧠 ĐẦU NÃO BACKEND (FLASK WEB SERVER)

### File 5: [app.py](file:///Users/nguyenbaongoc/Documents/millionaire/app.py)
Đây là file lớn nhất và quan trọng nhất của hệ thống. 

👉 **[Bấm vào đây để xem Tài Liệu Giải Thích Chi Tiết Mã Nguồn app.py (APP_PY_EXPLANATION.md)](file:///Users/nguyenbaongoc/Documents/millionaire/APP_PY_EXPLANATION.md)**

Dưới đây là các phần logic độc lập chính mà bạn cần học:

#### A. Khởi tạo App & Middleware `@login_required`
*   **Mục đích:** Bảo vệ các đường dẫn nhạy cảm (như trang chơi game, lịch sử, ví tiền). Nếu người dùng chưa đăng nhập, hệ thống lập tức đá họ về trang đăng ký/đăng nhập.
*   **Giải thích dòng code quan trọng:**
    ```python
    def login_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'username' not in session:
                return redirect('/auth')
            return f(*args, **kwargs)
        return decorated
    ```
    *   `@wraps(f)`: Giúp giữ lại tên gốc và docstring của hàm được bao bọc (decorator). Nếu thiếu cái này, Flask sẽ báo lỗi trùng tên hàm khi áp dụng cho nhiều route.
    *   `session`: Một dictionary lưu trữ thông tin tạm thời của phiên làm việc (cookie được mã hóa ở trình duyệt). Nếu có `'username'` trong `session` tức là người dùng đã đăng nhập thành công.

#### B. Cơ chế đăng ký / đăng nhập an toàn bằng `Bcrypt`
*   **Tại sao không lưu mật khẩu thô?** Nếu hacker tấn công và lấy được CSDL, toàn bộ tài khoản người dùng sẽ bị lộ. Bcrypt giải quyết việc này bằng cách tạo mã băm ngẫu nhiên.
*   **Giải thích dòng code quan trọng:**
    ```python
    # Đăng ký (Hashing):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    ```
    *   `password.encode('utf-8')`: Chuyển chuỗi chữ thường sang dạng bytes vì Bcrypt chỉ làm việc trên byte.
    *   `bcrypt.gensalt()`: Tạo ra một chuỗi "muối" ngẫu nhiên trộn vào mật khẩu trước khi băm, ngăn chặn tấn công dò bảng (rainbow table).
    ```python
    # Đăng nhập (Verification):
    is_valid = bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    ```
    *   `bcrypt.checkpw()`: Tự động trích xuất chuỗi muối từ mật khẩu đã băm trong DB, trộn vào mật khẩu người dùng vừa nhập rồi so sánh. Trả về `True` nếu khớp.

#### C. Gửi mã xác nhận qua Email (SMTP)
*   **Giải thích dòng code quan trọng:**
    ```python
    server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
    server.starttls()
    server.login(MAIL_USERNAME, MAIL_PASSWORD)
    ```
    *   `smtplib.SMTP(host, port)`: Khởi tạo kết nối tới server gửi thư (ví dụ: `smtp.gmail.com` cổng `587`).
    *   `server.starttls()`: Kích hoạt chế độ mã hóa bảo mật đường truyền TLS (Transport Layer Security). Toàn bộ nội dung email gửi đi sẽ không bị nghe lén trên đường truyền mạng.

#### D. Tích hợp Gemini AI tạo câu hỏi tự động
*   **Mục đích:** Gửi yêu cầu chi tiết đến Gemini và bắt AI sinh cấu trúc JSON chứa câu hỏi mà không có tạp chất chữ thừa bên ngoài.
*   **Giải thích dòng code quan trọng:**
    ```python
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )
    res_text = response.text
    # Parse chuỗi JSON nhận được từ AI thành danh sách Python
    questions = json.loads(res_text)
    ```
    *   `json.loads()`: Chuyển đổi một chuỗi văn bản định dạng JSON (String) thành đối tượng dữ liệu Python thực sự (List hoặc Dict) để chúng ta xử lý logic.
    *   **Cơ chế Fallback (Dự phòng):** Nếu API của Google bị lỗi hoặc hết hạn ngạch miễn phí, code sẽ có khối `try-except` để tự động chuyển sang đọc danh sách câu hỏi lưu cục bộ (`LOCAL_QUESTIONS`), đảm bảo game không bao giờ bị sập.

#### E. Xử lý Sepay Webhook nạp tiền tự động
*   **Mục đích:** Nhận tin nhắn thông báo chuyển khoản thành công từ Sepay.vn, đối chiếu chữ ký bảo mật và tự động cộng lượt chơi.
*   **Giải thích dòng code quan trọng:**
    ```python
    sepay_key = request.headers.get('x-sepay-secret-key')
    if sepay_key != WEBHOOK_SECRET:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    ```
    *   `request.headers.get()`: Lấy token bảo mật từ header của request.
    *   Nếu mã này không trùng khớp với `WEBHOOK_SECRET` đã lưu trong file `.env`, hệ thống từ chối xử lý ngay lập tức để ngăn chặn kẻ xấu giả lập giao dịch nạp tiền ảo.
    *   Nếu khớp, hệ thống tìm kiếm mã giao dịch `payment_ref` trong nội dung chuyển khoản, kiểm tra số tiền và cập nhật số lượt chơi trong bảng `user_wallets`.

---

## 4. 🌍 TIỆN ÍCH HỆ THỐNG & AUTOMATION

### File 6: [start.sh](file:///Users/nguyenbaongoc/Documents/millionaire/start.sh)
*   **Mục đích:** Tự động hóa việc dọn dẹp port bận, kích hoạt proxy công khai ngrok, lấy URL webhook tự động và khởi động Flask chỉ bằng một lệnh duy nhất.
*   **Giải thích dòng lệnh Bash quan trọng:**
    ```bash
    lsof -ti :5001 | xargs kill -9 2>/dev/null
    ```
    *   `lsof -ti :5001`: Tìm ID của tiến trình (PID) đang chạy chiếm dụng cổng `5001` (cổng mặc định của Flask).
    *   `xargs kill -9`: Gửi tín hiệu buộc tắt ngay lập tức tiến trình đó để giải phóng tài nguyên.
    *   `2>/dev/null`: Ẩn toàn bộ thông báo lỗi nếu cổng này vốn đã rảnh.

    ```bash
    ./ngrok http 5001 > /tmp/ngrok.log 2>&1 &
    NGROK_PID=$!
    ```
    *   `./ngrok http 5001`: Khởi tạo ngrok để ánh xạ cổng `5001` ra Internet.
    *   `> /tmp/ngrok.log 2>&1`: Đẩy toàn bộ log của ngrok vào file log tạm thời thay vì in tràn lan ra màn hình.
    *   `&`: Chạy lệnh này ngầm ở chế độ nền (background) để script có thể tiếp tục chạy lệnh tiếp theo.
    *   `NGROK_PID=$!`: Lưu lại ID tiến trình ngrok vừa chạy để khi chúng ta tắt Flask, script sẽ tự động tắt ngrok đi (`kill $NGROK_PID`).

    ```bash
    NGROK_PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "...")
    ```
    *   Gọi tới API cục bộ của ngrok để lấy địa chỉ URL `https://...` ngẫu nhiên vừa được cấp phát, giúp việc cài đặt webhook trên Sepay trở nên dễ dàng.

---

## 5. 🎨 FRONTEND LOGIC & HIỆU ỨNG (JAVASCRIPT)

### File 7: [static/js/game.js](file:///Users/nguyenbaongoc/Documents/millionaire/static/js/game.js)
Đây là file quản lý luồng game trên trình duyệt người dùng.

👉 **[Bấm vào đây để xem Tài Liệu Hướng Dẫn Học Lập Trình game.js (GAME_JS_EXPLANATION.md)](file:///Users/nguyenbaongoc/Documents/millionaire/GAME_JS_EXPLANATION.md)**

Dưới đây là các phần logic độc lập chính ở Client mà bạn cần học:

#### A. Gọi API bằng `fetch` và `async/await`
*   **Giải thích dòng code quan trọng:**
    ```javascript
    async function startGame() {
        const res = await fetch('/api/game/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player_name: playerName })
        });
        const data = await res.json();
    }
    ```
    *   `async`: Khai báo đây là một hàm bất tuần tự (asynchronous), cho phép sử dụng từ khóa `await`.
    *   `await fetch()`: Dừng thực thi tạm thời để chờ dữ liệu phản hồi từ server trả về qua mạng, giúp code trông thẳng hàng và dễ đọc hơn thay vì dùng callback lồng nhau phức tạp (Callback Hell).
    *   `JSON.stringify()`: Chuyển đổi đối tượng Javascript (Object) sang định dạng chuỗi JSON gửi đi.

#### B. SVG Timer Ring (Vòng tròn đếm ngược)
*   **Mục đích:** Vẽ và tạo hiệu ứng rút ngắn vòng tròn thời gian theo từng giây một cách mượt mà.
*   **Giải thích dòng code quan trọng:**
    ```javascript
    const circle = document.getElementById('timer-circle');
    circle.style.strokeDashoffset = 283 - (283 * timeLeft) / 30;
    ```
    *   `283`: Chu vi vòng tròn tính bằng pixel (tương ứng với thuộc tính `stroke-dasharray="283"` của thẻ `<circle>` trong HTML).
    *   `stroke-dashoffset`: Khoảng trống bắt đầu vẽ nét viền của vòng tròn. Khi thời gian giảm dần, khoảng cách offset này tăng lên khiến vòng tròn trông như đang co rút lại.

#### C. Synthesizer Âm Thanh bằng Web Audio API
*   **Tại sao không dùng file `.mp3`?** Tải file âm thanh qua mạng rất chậm, dễ bị trễ tiếng khi bấm nút và tốn băng thông server. Web Audio API cho phép tạo âm thanh bằng các thuật toán toán học phát ra trực tiếp từ trình duyệt.
*   **Giải thích dòng code quan trọng:**
    ```javascript
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    
    osc.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    osc.type = 'sine'; // Sóng hình sin mềm mại
    osc.frequency.setValueAtTime(440, audioCtx.currentTime); // Nốt La (A4)
    osc.start();
    osc.stop(audioCtx.currentTime + 0.5); // Phát trong 0.5 giây
    ```
    *   `AudioContext`: Bộ điều khiển âm thanh tổng của trình duyệt.
    *   `OscillatorNode` (osc): Bộ dao động sóng âm. Nó tạo ra các loại tần số sóng cơ bản (`sine`, `square`, `triangle`, `sawtooth`) quyết định âm sắc.
    *   `GainNode`: Bộ tăng giảm âm lượng.
    *   `setValueAtTime(440, ...)`: Thiết lập tần số nốt nhạc. Bằng cách thay đổi tần số theo thời gian, ta có thể tạo ra các tiếng động kịch tính như tiếng đếm giây bíp bíp, tiếng đúng (tần số tăng dần), tiếng sai (tần số tụt sâu đột ngột).

---

## 6. 🖼️ GIAO DIỆN HIỂN THỊ (HTML TEMPLATES)

### File 8, 9, 10: `index.html`, `auth.html`, `shop.html`
*   **Mục đích:** Cung cấp khung xương HTML và hệ thống CSS tạo nên phong cách **Maximalism & Dopamine**.

#### A. Thiết lập SEO và Trải nghiệm di động tốt
*   **Giải thích các thẻ đặc biệt trong phần `<head>`:**
    ```html
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    ```
    *   `user-scalable=no`: Ngăn chặn người dùng zoom màn hình khi nhấp đúp hoặc dùng hai ngón tay trên điện thoại, giữ cho tỷ lệ giao diện game luôn chuẩn như app di động native.
    *   `apple-mobile-web-app-capable`: Cho phép thiết bị iOS ẩn thanh công cụ của Safari khi người dùng lưu trang web ra màn hình chính dưới dạng PWA.

#### B. Các Hiệu Ứng Chuyển Động CSS (Keyframes Animation)
Giao diện dự án rất rực rỡ nhờ vào các hiệu ứng nền động tự động chạy:
```css
@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-15px); }
}
.floating-element {
    animation: float 4s ease-in-out infinite;
}
```
*   `@keyframes`: Định nghĩa một chuỗi trạng thái chuyển động. Ở đây, tại thời điểm giữa chu kỳ (50%), phần tử sẽ bị dịch chuyển lên trên 15 pixel (`translateY(-15px)`).
*   `infinite`: Chạy lặp đi lặp lại vô hạn lần.
*   `ease-in-out`: Chuyển động tăng tốc ở đầu và giảm tốc ở cuối chu kỳ giúp hiệu ứng trông mượt mà và tự nhiên hơn.

---

## 🛠️ PHƯƠNG PHÁP HỌC TỐT NHẤT TỪ DỰ ÁN NÀY (HỌC BẰNG THỰC HÀNH)

1.  **Bước 1 - Đọc hiểu:** Đọc tài liệu này song song với việc mở file mã nguồn tương ứng trong VS Code để xem vị trí của từng đoạn code đã giải thích.
2.  **Bước 2 - Sửa thử:** Thử thay đổi các tham số nhỏ trong code để cảm nhận kết quả:
    *   *Ví dụ 1:* Sửa thời gian đếm ngược trong `game.js` từ `30` giây thành `15` giây và chạy lại.
    *   *Ví dụ 2:* Đổi tone nhạc trong Web Audio API bằng cách thay đổi tần số (ví dụ từ `440` lên `880`) để tạo ra tiếng bíp cao hơn.
    *   *Ví dụ 3:* Đổi tên các mức tiền thưởng trong bảng `PRIZE_LEVELS` ở `app.py` và `game.js` xem hệ thống cập nhật ra sao.
3.  **Bước 3 - Viết lại:** Tự tay viết lại từng hàm nhỏ (nhâu hàm Auth, hàm gửi Mail, hàm check đáp án) vào một file nháp để ghi nhớ cú pháp.
=======
## 🛠️ Công nghệ sử dụng

| Layer | Công nghệ |
|-------|-----------|
| **Backend** | Python 3.10+, Flask 3.1, Flask-CORS |
| **Database** | PostgreSQL (psycopg2-binary) |
| **AI** | Google Gemini Flash (google-genai) |
| **Auth** | bcrypt (hash mật khẩu), Flask Session, SMTP (quên mật khẩu) |
| **Thanh toán** | SePay Webhook, VietQR, HMAC-SHA256 |
| **Frontend** | HTML5, CSS3 (Custom Properties, Animations), Vanilla JavaScript |
| **PWA** | Web App Manifest, Service Worker |
| **Fonts** | Outfit, DM Sans, Bungee (Google Fonts) |
| **Audio** | Web Audio API |
| **Deploy** | Gunicorn, ngrok (cho webhook local) |

---

## 🚀 Hướng dẫn cài đặt & chạy

### 1. Yêu cầu hệ thống

- **Python 3.10+**
- **PostgreSQL** đang chạy (local hoặc cloud như Supabase, Neon, Render)
- **Gemini API Key** — lấy tại [Google AI Studio](https://aistudio.google.com/apikey)

### 2. Clone repository

```bash
git clone https://github.com/baongocdzvc/Game-who-want-to-be-a-millionaire.git
cd Game-who-want-to-be-a-millionaire
```

### 3. Cài đặt thư viện Python

```bash
pip install -r requirements.txt
```

Các thư viện chính:
- `flask==3.1.1` — Framework web
- `flask-cors==5.0.1` — Cross-Origin Resource Sharing
- `google-genai` — Gemini AI SDK
- `python-dotenv` — Đọc file .env
- `psycopg2-binary` — PostgreSQL driver
- `bcrypt` — Mã hóa mật khẩu
- `gunicorn` — WSGI server cho production

### 4. Cấu hình biến môi trường

Tạo file `.env` trong thư mục gốc:

```env
# === AI ===
GEMINI_API_KEY=your_gemini_api_key_here

# === DATABASE ===
# Cách 1: Dùng DATABASE_URL (khuyến nghị cho cloud database)
DATABASE_URL=postgresql://user:password@host:port/database

# Cách 2: Hoặc cấu hình từng tham số
DB_HOST=localhost
DB_PORT=5432
DB_NAME=millionaire
DB_USER=postgres
DB_PASSWORD=123456

# === SESSION ===
SECRET_KEY=your-secret-key-here

# === EMAIL (Quên mật khẩu) ===
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_SENDER=Ai La Trieu Phu <your_email@gmail.com>

# === SEPAY (Thanh toán) ===
SEPAY_BANK_CODE=MBBank
SEPAY_ACCOUNT_NO=0123456789
SEPAY_ACCOUNT_NAME=AI LA TRIEU PHU
WEBHOOK_SECRET=your-webhook-secret

# === NGROK (Cho webhook local) ===
NGROK_AUTHTOKEN=your_ngrok_authtoken
```

### 5. Khởi tạo database

Database schema sẽ tự động được tạo khi chạy `app.py` lần đầu. Bạn cũng có thể khởi tạo thủ công:

```bash
python database.py
```

Lệnh này sẽ tạo:
- 8 bảng: `users`, `user_passwords`, `rankings`, `game_history`, `password_reset_codes`, `user_wallets`, `shop_transactions`, `webhook_logs`
- Các index tối ưu truy vấn
- Trigger tự động cập nhật `win_rate`
- Dữ liệu mẫu (user `player01`)

### 6. Chạy server

**Cách đơn giản (không webhook thanh toán):**

```bash
python app.py
```

Server chạy tại: `http://localhost:5001`

**Cách đầy đủ (có webhook thanh toán qua ngrok):**

```bash
bash start.sh
```

Script sẽ tự động:
1. Kiểm tra `NGROK_AUTHTOKEN` trong `.env`
2. Cấu hình và khởi động ngrok tunnel
3. Hiển thị URL công khai để cấu hình webhook trên SePay
4. Khởi động Flask server

### 7. Cấu hình Webhook SePay (nếu dùng thanh toán)

Sau khi chạy `bash start.sh`, truy cập [SePay.vn](https://sepay.vn) và cấu hình:
- **URL Webhook**: `{NGROK_PUBLIC_URL}/api/shop/webhook`
- **Xác thực**: Apikey
- **Giá trị**: Giá trị `WEBHOOK_SECRET` trong file `.env`

---

## 📡 API Endpoints

### Xác thực (Auth)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/auth` | Trang đăng nhập / đăng ký |
| `POST` | `/api/auth/register` | Đăng ký tài khoản mới |
| `POST` | `/api/auth/login` | Đăng nhập |
| `POST` | `/api/auth/logout` | Đăng xuất |
| `GET` | `/api/auth/me` | Kiểm tra trạng thái đăng nhập |
| `POST` | `/api/auth/forgot-password` | Gửi mã xác nhận quên mật khẩu |
| `POST` | `/api/auth/verify-reset-code` | Xác thực mã & đặt lại mật khẩu |

### Game

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/` | Trang chủ game (yêu cầu đăng nhập) |
| `POST` | `/api/game/start` | Bắt đầu ván chơi mới |
| `POST` | `/api/game/answer` | Trả lời câu hỏi |
| `POST` | `/api/game/lifeline` | Sử dụng quyền trợ giúp |
| `POST` | `/api/game/stop` | Dừng cuộc chơi |
| `POST` | `/api/game/timeout` | Hết giờ trả lời |
| `GET` | `/api/game/history` | Lịch sử chơi của tôi |

### Chatbot & Dịch thuật

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `POST` | `/api/chatbot` | Chat với MC Trợ Lý AI |
| `POST` | `/api/translate` | Dịch câu hỏi sang ngôn ngữ khác |

### Cửa hàng (Shop)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/api/shop/wallet` | Xem ví (lượt chơi, trợ giúp dự phòng) |
| `POST` | `/api/shop/create-order` | Tạo đơn hàng mua vật phẩm |
| `GET` | `/api/shop/check-status` | Kiểm tra trạng thái đơn hàng |
| `GET` | `/api/shop/history` | Lịch sử mua hàng |
| `POST` | `/api/shop/webhook` | Webhook SePay nhận thông báo thanh toán |

### Bảng xếp hạng & Debug

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/api/leaderboard` | Bảng xếp hạng Top 10 |
| `GET` | `/api/debug/status` | Trạng thái hệ thống (debug) |
| `GET` | `/api/debug/webhooks` | Nhật ký webhook (debug) |
| `GET` | `/api/debug/transaction/<ref>` | Chi tiết giao dịch (debug) |

---

## 🗄️ Cấu trúc Database

```
┌─────────────────────┐     ┌──────────────────────────┐
│       users          │     │    user_passwords         │
├─────────────────────┤     ├──────────────────────────┤
│ user_id (PK, SERIAL)│◄────│ user_id (FK, UNIQUE)      │
│ username (UNIQUE)   │     │ password_hash             │
│ email (UNIQUE)      │     │ salt                      │
│ full_name           │     │ last_changed              │
│ avatar_url          │     │ must_change               │
│ is_active           │     └──────────────────────────┘
│ created_at          │
│ updated_at          │     ┌──────────────────────────┐
└───────┬─────────────┘     │    user_wallets           │
        │                   ├──────────────────────────┤
        │                   │ user_id (PK, FK)          │
        │                   │ game_turns (default: 3)   │
        │                   │ bonus_lifelines (default:0)│
        │                   │ updated_at                │
        │                   └──────────────────────────┘
        │
        ├───┌──────────────────────┐
        │   │     rankings          │
        │   ├──────────────────────┤
        │   │ ranking_id (PK)       │
        │   │ user_id (FK, UNIQUE)  │
        │   │ total_score           │
        │   │ total_wins / losses   │
        │   │ win_rate (auto)       │
        │   │ rank_title / points   │
        │   └──────────────────────┘
        │
        ├───┌──────────────────────┐
        │   │    game_history       │
        │   ├──────────────────────┤
        │   │ history_id (PK)       │
        │   │ user_id (FK)          │
        │   │ game_mode / result    │
        │   │ score / duration_sec  │
        │   │ metadata (JSONB)      │
        │   │ played_at             │
        │   └──────────────────────┘
        │
        ├───┌──────────────────────────┐
        │   │  shop_transactions        │
        │   ├──────────────────────────┤
        │   │ transaction_id (PK)       │
        │   │ user_id (FK)              │
        │   │ item_type / quantity      │
        │   │ total_price               │
        │   │ payment_ref (UNIQUE)      │
        │   │ status (pending/paid)     │
        │   └──────────────────────────┘
        │
        ├───┌──────────────────────────┐
        │   │  password_reset_codes     │
        │   ├──────────────────────────┤
        │   │ code_id (PK)              │
        │   │ user_id (FK)              │
        │   │ code (6 digits)           │
        │   │ expires_at / is_used      │
        │   └──────────────────────────┘
        │
        └───┌──────────────────────────┐
            │    webhook_logs           │
            ├──────────────────────────┤
            │ log_id (PK)               │
            │ ip_address / headers      │
            │ payload (JSONB)           │
            │ is_authenticated          │
            │ payment_ref / matched     │
            │ error_message             │
            └──────────────────────────┘
```

**Trigger tự động**: `trg_win_rate` — tự động tính toán `win_rate` mỗi khi bảng `rankings` được UPDATE.

---

## 🎯 Luật chơi

1. Mỗi người chơi có **3 lượt chơi miễn phí** khi đăng ký
2. Mỗi ván gồm **15 câu hỏi** từ dễ đến khó
3. Mỗi câu có **30 giây** suy nghĩ
4. Có **3 quyền trợ giúp**, mỗi quyền dùng được 1 lần trong một ván:
   - **50:50** — Loại bỏ 2 đáp án sai
   - **Gọi điện** — Người thân gợi ý (70% chính xác)
   - **Hỏi khán giả** — Xem biểu đồ bình chọn của khán giả
5. **2 mốc an toàn** ở câu 5 và câu 10 — nếu trả lời sai, vẫn nhận tiền ở mốc gần nhất đã vượt qua
6. Có thể **dừng cuộc chơi** bất kỳ lúc nào để mang về tiền thưởng hiện tại
7. Trả lời đúng tất cả 15 câu → **TRIỆU PHÚ** — nhận 150.000.000 đ!

---

## 📱 Cài PWA trên điện thoại

- **iPhone**: Mở Safari → Nhấn nút Chia sẻ → "Thêm vào Màn hình chính"
- **Android**: Mở Chrome → Nhấn menu ⋮ → "Cài đặt ứng dụng"

---

## 🤝 Đóng góp

Mọi đóng góp đều được hoan nghênh! Bạn có thể:

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/amazing-feature`)
3. Commit thay đổi (`git commit -m 'Add amazing feature'`)
4. Push lên branch (`git push origin feature/amazing-feature`)
5. Mở Pull Request

---

## 📄 License

Dự án này được phân phối dưới mục đích học tập và tham khảo. Vui lòng tôn trọng bản quyền của gameshow gốc *Who Wants To Be A Millionaire*.

---

<p align="center">
  <strong>🎯 Ai Là Triệu Phú — Sẵn sàng chinh phục 150 triệu? 💰</strong>
</p>
