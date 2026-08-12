# 📖 TÀI LIỆU HƯỚNG DẪN HỌC LẬP TRÌNH CHI TIẾT TỪNG FILE — DỰ ÁN AI LÀ TRIỆU PHÚ

Tài liệu này được thiết kế đặc biệt để giúp bạn hiểu sâu sắc **từng dòng code**, **từng câu lệnh**, và **luồng tư duy** đằng sau mỗi file trong dự án "Ai Là Triệu Phú - AI Edition". Hãy xem đây là một cuốn cẩm nang tự học (self-study guide) từ cơ bản đến nâng cao.

---

## 🗺️ TỔNG QUAN KIẾN TRÚC DỰ ÁN (SYSTEM ARCHITECTURE)

Dự án được xây dựng theo mô hình **Client-Server (Frontend - Backend)** kết hợp với cơ sở dữ liệu quan hệ **PostgreSQL** và **Gemini AI**:

```mermaid
graph TD
    Client[Browser Frontend: HTML/CSS/JS] <-->|HTTP REST API / JSON| Server[Flask Backend: app.py]
    Server <-->|SQL Queries / psycopg2 Pool| DB[(PostgreSQL Database)]
    Server <-->|Google GenAI SDK| Gemini[Gemini 1.5 Flash AI API]
    Sepay[Sepay.vn Payment Gateway] --->|Webhook POST| Server
```

---

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
