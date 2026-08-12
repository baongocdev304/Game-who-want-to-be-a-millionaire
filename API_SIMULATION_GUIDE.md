# 🔄 MÔ PHỎNG CÁCH GAME GỌI API — LUỒNG REQUEST/RESPONSE

Tài liệu này mô phỏng **chính xác từng bước** của một ván chơi hoàn chỉnh, từ lúc người dùng bấm "Bắt đầu" cho đến khi kết thúc.  
Mỗi mũi tên `→` thể hiện một lần giao tiếp thực sự giữa trình duyệt và server Flask.

---

## 🗺️ SƠ ĐỒ TỔNG QUAN CÁC API TRONG GAME

```
TRÌNH DUYỆT (game.js)              SERVER FLASK (app.py)
─────────────────────              ──────────────────────
[1] Bắt đầu chơi    ──POST──►  /api/game/start
[2] Chọn đáp án     ──POST──►  /api/game/answer
[3] Hết giờ         ──POST──►  /api/game/timeout
[4] Trợ giúp 50/50  ──POST──►  /api/game/lifeline
[5] Trợ giúp gọi DT ──POST──►  /api/game/lifeline
[6] Trợ giúp khán g ──POST──►  /api/game/lifeline
[7] Dừng cuộc chơi  ──POST──►  /api/game/stop
[8] Chat với MC     ──POST──►  /api/chatbot
[9] Dịch câu hỏi   ──POST──►  /api/translate
[10] Kiểm tra ví    ──GET───►  /api/shop/wallet
[11] Lưu bảng XH   ──POST──►  /api/leaderboard
```

---

## 1️⃣ API BẮT ĐẦU GAME — `/api/game/start`

**Khi nào gọi?** Người chơi nhập tên và bấm nút **"BẮT ĐẦU CHƠI"**

### 📤 game.js GỬI LÊN SERVER:
```javascript
// game.js dòng 87-91
const res = await fetch('/api/game/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        player_name: "Nguyễn Bảo Ngọc"   // Tên nhập từ ô input
    })
});
```

**Nội dung thực sự gửi đi (HTTP Request):**
```
POST /api/game/start HTTP/1.1
Content-Type: application/json

{
  "player_name": "Nguyễn Bảo Ngọc"
}
```

### ⚙️ SERVER (app.py) XỬ LÝ:
```
1. Kiểm tra đăng nhập: session.get('user_id') → có user_id không?
2. Kiểm tra số lượt chơi trong ví: SELECT game_turns FROM user_wallets
3. Nếu game_turns <= 0  →  trả về lỗi "hết lượt chơi"
4. Trừ 1 lượt: UPDATE user_wallets SET game_turns = game_turns - 1
5. Gọi Gemini AI sinh 15 câu hỏi mới
6. Tạo mã phiên duy nhất: session_id = uuid.uuid4()
7. Lưu 15 câu + trạng thái game vào bộ nhớ (dict `sessions`)
8. Trả câu hỏi số 1 về (KHÔNG kèm đáp án đúng!)
```

### 📥 SERVER TRẢ VỀ CHO game.js:
```json
{
  "success": true,
  "session_id": "a3f7c2d1-8b4e-4a9f-b2c1-d5e6f7a8b9c0",
  "player_name": "Nguyễn Bảo Ngọc",
  "question_number": 1,
  "total_questions": 15,
  "current_prize": "0 đ",
  "question": {
    "difficulty": "easy",
    "question": "Thủ đô của Việt Nam là thành phố nào?",
    "answers": ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Huế"]
  },
  "prize_levels": ["200.000 đ", "400.000 đ", ...],
  "milestones": [4, 9]
}
```

### 🖥️ game.js NHẬN VÀ LÀM GÌ:
```javascript
// game.js dòng 94-108
if (data.success) {
    sessionId = data.session_id;     // Lưu ID phiên để dùng cho mọi API về sau
    currentQuestion = 0;
    switchScreen('game-screen');     // Chuyển sang màn hình game
    displayQuestion(data.question, data.question_number);  // Hiện câu hỏi 1
    addBotMessage("Chào mừng đến với Ai Là Triệu Phú! 🎉");
}
```

> **💡 Lưu ý quan trọng:** Server KHÔNG bao giờ gửi chỉ số đáp án đúng (`correct`) về client. Điều này ngăn người chơi mở DevTools xem Network tab để gian lận!

---

## 2️⃣ API CHỌN ĐÁP ÁN — `/api/game/answer`

**Khi nào gọi?** Người chơi bấm vào 1 trong 4 ô đáp án A/B/C/D

### 📤 game.js GỬI LÊN SERVER (sau 2 giây kịch tính):
```javascript
// game.js dòng 220-224
const res = await fetch('/api/game/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        session_id: "a3f7c2d1-8b4e-4a9f-b2c1-d5e6f7a8b9c0",  // ID phiên đã lưu
        answer: 0    // Số chỉ mục đáp án: 0=A, 1=B, 2=C, 3=D
    })
});
```

### ⚙️ SERVER XỬ LÝ:
```
1. Tra cứu sessions[session_id] → lấy câu hỏi hiện tại
2. So sánh answer với question['correct']
3a. Nếu ĐÚNG:  tăng current_question += 1, cập nhật prize
3b. Nếu SAI:   đánh dấu game kết thúc, tính tiền thưởng theo mốc an toàn
4. Ghi lịch sử vào DB (game_history, rankings)
```

### 📥 SERVER TRẢ VỀ (Trường hợp TRẢ LỜI ĐÚNG, chưa hết game):
```json
{
  "success": true,
  "is_correct": true,
  "correct_answer": 0,
  "game_over": false,
  "won": false,
  "question_number": 2,
  "current_prize": "200.000 đ",
  "next_question": {
    "difficulty": "easy",
    "question": "Bánh chưng thường được gói bằng lá gì?",
    "answers": ["Lá dong", "Lá chuối", "Lá sen", "Lá dừa"]
  }
}
```

### 📥 SERVER TRẢ VỀ (Trường hợp TRẢ LỜI SAI):
```json
{
  "success": true,
  "is_correct": false,
  "correct_answer": 2,
  "game_over": true,
  "won": false,
  "prize": "2.000.000 đ",
  "correct_count": 5,
  "total_time": 87
}
```

### 📥 SERVER TRẢ VỀ (Trường hợp THẮNG CUỘC — vượt câu 15):
```json
{
  "success": true,
  "is_correct": true,
  "correct_answer": 1,
  "game_over": true,
  "won": true,
  "prize": "150.000.000 đ",
  "correct_count": 15,
  "total_time": 342
}
```

### 🖥️ game.js NHẬN VÀ LÀM GÌ:
```javascript
// game.js dòng 229-253
if (data.is_correct) {
    btn.classList.add('correct');  // Tô xanh ô đáp án đúng
    playSound('correct');          // Tiếng chuông đúng
    createConfetti();              // Pháo hoa giấy
    if (data.game_over && data.won) {
        showResult(true, true, data);  // Màn hình CHIẾN THẮNG
    } else {
        currentQuestion++;
        displayQuestion(data.next_question, data.question_number);  // Câu tiếp
    }
} else {
    btn.classList.add('wrong');    // Tô đỏ ô sai
    document.getElementById('answer-' + data.correct_answer).classList.add('correct');
    showResult(false, false, data);  // Màn hình THẤT BẠI
}
```

---

## 3️⃣ API HẾT GIỜ — `/api/game/timeout`

**Khi nào gọi?** Đồng hồ đếm ngược về 0 mà người chơi chưa chọn đáp án

### 📤 game.js GỬI:
```javascript
// game.js dòng 193-197
const res = await fetch('/api/game/timeout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        session_id: "a3f7c2d1-8b4e-4a9f-b2c1-d5e6f7a8b9c0"
    })
});
```

### 📥 SERVER TRẢ VỀ:
```json
{
  "success": true,
  "correct_answer": 2,
  "game_over": true,
  "prize": "0 đ",
  "correct_count": 0,
  "total_time": 30
}
```

### 🖥️ game.js NHẬN VÀ LÀM GÌ:
```javascript
// Tô sáng đáp án đúng để người chơi biết
document.getElementById('answer-' + data.correct_answer).classList.add('correct');
addBotMessage('⏰ Hết giờ! Đáp án đúng là ' + ['A','B','C','D'][data.correct_answer]);
setTimeout(() => showResult(false, false, data), 2500);
```

---

## 4️⃣ API QUYỀN TRỢ GIÚP — `/api/game/lifeline`

**Khi nào gọi?** Người chơi bấm một trong 3 nút trợ giúp: ✂️50:50 / 📞Gọi điện / 👥Khán giả

### 📤 game.js GỬI (ví dụ: dùng 50/50):
```javascript
// game.js dòng 288-293
const res = await fetch('/api/game/lifeline', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        session_id: "a3f7c2d1-8b4e-4a9f-b2c1-d5e6f7a8b9c0",
        type: "5050"   // Hoặc "phone" hoặc "audience"
    })
});
```

### 📥 SERVER TRẢ VỀ (50/50 — Loại 2 đáp án sai):
```json
{
  "success": true,
  "type": "5050",
  "removed": [1, 3]
}
```
> game.js nhận và ẩn đi các ô đáp án B (index 1) và D (index 3)

### 📥 SERVER TRẢ VỀ (Gọi điện cho người thân):
```json
{
  "success": true,
  "type": "phone",
  "suggestion": 0,
  "confidence": 85
}
```
> game.js hiển thị modal: *"Đáp án A (85% chắc chắn)"*

### 📥 SERVER TRẢ VỀ (Hỏi ý kiến khán giả):
```json
{
  "success": true,
  "type": "audience",
  "percents": [62, 12, 18, 8]
}
```
> game.js vẽ biểu đồ cột: A=62%, B=12%, C=18%, D=8%

### 🔁 Luồng đặc biệt — Dùng trợ giúp đã cũ bằng lượt dự phòng từ ví:
```javascript
// game.js dòng 265-286
// Nếu nút đã 'used', kiểm tra ví có bonus_lifelines không
const wRes = await fetch('/api/shop/wallet');  // GET ví
const wData = await wRes.json();
const bonusCount = wData.bonus_lifelines;

if (bonusCount <= 0) {
    alert('Không còn lượt trợ giúp dự phòng nào trong ví!');
    return;
}
// Nếu có, hỏi xác nhận rồi gọi API lifeline như bình thường
```

---

## 5️⃣ API DỪNG CUỘC CHƠI — `/api/game/stop`

**Khi nào gọi?** Người chơi chủ động bấm nút **"DỪNG"** để bảo toàn tiền thưởng

### 📤 game.js GỬI:
```javascript
// game.js dòng 337-341
const res = await fetch('/api/game/stop', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
});
```

### 📥 SERVER TRẢ VỀ:
```json
{
  "success": true,
  "prize": "6.000.000 đ",
  "correct_count": 6,
  "total_time": 155
}
```

---

## 6️⃣ API CHAT VỚI MC TRỢ LÝ — `/api/chatbot`

**Khi nào gọi?** Người chơi gõ tin nhắn vào khung chat và bấm Gửi

### 📤 game.js GỬI:
```javascript
// game.js dòng 480-484
const res = await fetch('/api/chatbot', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: "MC ơi, câu này khó quá, gợi ý mình với!",
        session_id: "a3f7c2d1-8b4e-4a9f-b2c1-d5e6f7a8b9c0"
    })
});
```

### 📥 SERVER TRẢ VỀ:
```json
{
  "success": true,
  "reply": "Haha, câu này không khó lắm đâu bạn ơi! Hãy nghĩ đến những kiến thức lịch sử cơ bản mà bạn đã học nhé. Tôi tin bạn làm được! 💪"
}
```

### ⚙️ Server xử lý như thế nào:
Server gửi cả **ngữ cảnh game** (đang ở câu mấy, tiền thưởng bao nhiêu) lẫn **tin nhắn người dùng** vào Gemini AI để AI trả lời như MC thực sự đang theo dõi ván chơi.

---

## 7️⃣ API DỊCH CÂU HỎI — `/api/translate`

**Khi nào gọi?** Người chơi bấm nút dịch câu hỏi sang ngôn ngữ khác

### 📤 game.js GỬI:
```javascript
// game.js dòng 517-521
const res = await fetch('/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        session_id: "a3f7c2d1-8b4e-4a9f-b2c1-d5e6f7a8b9c0",
        target_lang: "en"   // "en" = Tiếng Anh, "zh" = Tiếng Trung, v.v.
    })
});
```

### 📥 SERVER TRẢ VỀ:
```json
{
  "success": true,
  "translated": {
    "question": "What is the capital of Vietnam?",
    "answers": ["Hanoi", "Ho Chi Minh City", "Da Nang", "Hue"]
  }
}
```

### 🖥️ game.js CẬP NHẬT GIAO DIỆN:
```javascript
// Thay nội dung câu hỏi và 4 đáp án trực tiếp trên DOM
document.getElementById('question-text').textContent = data.translated.question;
for (let i = 0; i < 4; i++) {
    document.getElementById('text-' + i).textContent = data.translated.answers[i];
}
```

---

## 8️⃣ API KIỂM TRA VÍ — `/api/shop/wallet`

**Khi nào gọi?** Khi người chơi muốn dùng trợ giúp đã dùng rồi hoặc khi mở màn hình chào

### 📤 game.js GỬI (GET request — không có body):
```javascript
// game.js dòng 267
const wRes = await fetch('/api/shop/wallet');
```

### 📥 SERVER TRẢ VỀ:
```json
{
  "success": true,
  "game_turns": 3,
  "bonus_lifelines": 2,
  "updated_at": "2026-06-02T10:30:00"
}
```

---

## 9️⃣ API LƯU BẢNG XẾP HẠNG — `/api/leaderboard`

**Khi nào gọi?** Tự động gọi ngay khi kết thúc ván chơi (dù thắng hay thua)

### 📤 game.js GỬI:
```javascript
// game.js dòng 380-389
await fetch('/api/leaderboard', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        player_name: "Nguyễn Bảo Ngọc",
        correct_count: 10,
        prize: "22.000.000 đ",
        total_time: 245
    })
});
```

---

## 🔄 MÔ PHỎNG MỘT VÁN CHƠI HOÀN CHỈNH (TIMELINE)

```
Thời điểm   Hành động người chơi        API được gọi             Kết quả
──────────  ─────────────────────────  ──────────────────────    ────────────────────────
T+0s        Bấm "Bắt Đầu Chơi"        POST /api/game/start  →   Nhận câu hỏi 1
T+8s        Bấm đáp án A (đúng)        POST /api/game/answer →   Nhận câu hỏi 2, tiền 200k
T+20s       Dùng 50/50                 POST /api/game/lifeline → Ẩn 2 đáp án sai
T+35s       Bấm đáp án C (đúng)        POST /api/game/answer →   Nhận câu hỏi 3, tiền 400k
T+42s       Chat "MC ơi tôi mệt quá"   POST /api/chatbot     →   MC động viên
T+60s       Hết giờ ở câu 4            POST /api/game/timeout →  Hiện đáp án đúng → Thua
T+62s       (Tự động)                  POST /api/leaderboard →   Lưu kết quả vào DB
```

---

## 🧪 TỰ THỬ GỌI API BẰNG `curl` (Không Cần Mở Game)

Bạn có thể giả lập game mà không cần mở trình duyệt, chỉ dùng terminal:

### Bước 1: Đăng nhập để lấy session cookie
```bash
curl -c cookies.txt -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "player01", "password": "SecurePass123"}'
```

### Bước 2: Bắt đầu game
```bash
curl -b cookies.txt -X POST http://localhost:5001/api/game/start \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Học Viên Test"}'
```
*(Server sẽ trả về `session_id` — copy lại để dùng ở bước tiếp theo)*

### Bước 3: Trả lời câu hỏi (đáp án B = index 1)
```bash
curl -b cookies.txt -X POST http://localhost:5001/api/game/answer \
  -H "Content-Type: application/json" \
  -d '{"session_id": "PASTE_SESSION_ID_HERE", "answer": 1}'
```

### Bước 4: Dùng trợ giúp 50/50
```bash
curl -b cookies.txt -X POST http://localhost:5001/api/game/lifeline \
  -H "Content-Type: application/json" \
  -d '{"session_id": "PASTE_SESSION_ID_HERE", "type": "5050"}'
```

### Bước 5: Chat với MC
```bash
curl -b cookies.txt -X POST http://localhost:5001/api/chatbot \
  -H "Content-Type: application/json" \
  -d '{"session_id": "PASTE_SESSION_ID_HERE", "message": "Chào MC!"}'
```

### Bước 6: Mua lượt chơi / Trợ giúp trong Cửa hàng
Khi người chơi muốn mua thêm lượt chơi (`game_turn` - 5.000đ/lượt) hoặc lượt trợ giúp dự phòng (`bonus_lifeline` - 2.000đ/lượt), giao diện cửa hàng sẽ gửi yêu cầu tạo đơn hàng.

**Gọi API tạo đơn hàng:**
```bash
curl -b cookies.txt -X POST http://localhost:5001/api/shop/create-order \
  -H "Content-Type: application/json" \
  -d '{"item_type": "game_turn", "quantity": 5}'
```

**Server trả về:**
```json
{
  "success": true,
  "txn_id": "AMT_1780089184_D2A1C3",
  "payment_ref": "AMT_1780089184_D2A1C3",
  "total_price": 25000,
  "qr_url": "https://img.vietqr.io/image/MB-0392817283-compact2.png?amount=25000&addInfo=AMT_1780089184_D2A1C3&accountName=NGUYEN%20BAO%20NGOC",
  "bank_code": "MB",
  "account_no": "0392817283",
  "account_name": "NGUYEN BAO NGOC"
}
```
> **Giải thích:** Server sinh mã giao dịch duy nhất dạng `AMT_TIMESTAMP_HEX` (đóng vai trò là nội dung chuyển khoản). Đường dẫn `qr_url` là ảnh mã QR theo chuẩn VietQR giúp người chơi quét mã chuyển tiền nhanh.

---

### Bước 7: Trình duyệt liên tục kiểm tra trạng thái đơn hàng (Polling)
Trong lúc người chơi đang quét mã QR trên màn hình, Javascript ở phía Client sẽ tự động gọi API này mỗi 2 giây một lần để kiểm tra xem hệ thống đã ghi nhận thanh toán chưa.

**Gọi API kiểm tra trạng thái đơn hàng:**
```bash
curl -b cookies.txt "http://localhost:5001/api/shop/check-status?ref=AMT_1780089184_D2A1C3"
```

**Kết quả khi chưa thanh toán:**
```json
{
  "success": true,
  "status": "pending"
}
```

**Kết quả sau khi thanh toán thành công:**
```json
{
  "success": true,
  "status": "paid"
}
```
> **Giao diện làm gì?** Ngay khi nhận được trạng thái `"status": "paid"`, giao diện cửa hàng sẽ tắt popup mã QR, hiện thông báo chúc mừng và cập nhật lại số dư ví mới của người chơi.

---

### Bước 8: Giả lập Webhook SePay thông báo thanh toán
Khi người chơi chuyển tiền vào ngân hàng, hệ thống cổng thanh toán SePay sẽ tự động phát hiện biến động số dư và gửi một HTTP POST (gọi là Webhook) tới Server Flask của bạn để xác nhận giao dịch.

#### Cách 1: Gửi tín hiệu Test Webhook (Để kiểm tra kết nối giữa SePay và Server)
```bash
curl -X POST http://localhost:5001/api/webhook/sepay \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-123" \
  -d '{"content": "sepay test", "id": 9999, "transferAmount": 0, "code": "SEPAYTEST"}'
```
*Kết quả trả về:* `{"success": true, "message": "Kết nối webhook thành công! (Test Webhook)"}`

#### Cách 2: Giả lập thanh toán thật cho đơn hàng `AMT_1780089184_D2A1C3` ở Bước 6
```bash
curl -X POST http://localhost:5001/api/webhook/sepay \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-123" \
  -d '{
    "id": 1234567,
    "content": "Chuyển tiền mua lượt chơi AMT_1780089184_D2A1C3",
    "transferAmount": 25000,
    "transferType": "in",
    "gateway": "MBBank"
  }'
```

**Server xử lý như thế nào?**
1. Xác thực API Key bảo mật (`X-API-Key` khớp với `WEBHOOK_SECRET` trong file `.env`).
2. Dùng Regex lọc trong chuỗi nội dung chuyển khoản (`content`) để trích xuất ra mã đơn hàng `AMT_1780089184_D2A1C3`.
3. Kiểm tra số tiền chuyển thực tế (`transferAmount` = 25000) có khớp với số tiền cần thanh toán trong cơ sở dữ liệu của đơn hàng đó không.
4. Cập nhật trạng thái đơn hàng trong database thành `paid`.
5. Cộng số lượt chơi tương ứng (`+5` lượt chơi) vào ví `user_wallets` của người dùng.

---

### Bước 9: Xem lịch sử giao dịch và ví
Sau khi mua hàng, bạn có thể kiểm tra xem ví đã được cộng tiền hay chưa và xem lịch sử các lần giao dịch.

**Xem số dư ví:**
```bash
curl -b cookies.txt http://localhost:5001/api/shop/wallet
```
*Kết quả:* `{"success":true,"game_turns":8,"bonus_lifelines":2}` (tăng thêm 5 lượt chơi so với ban đầu).

**Xem lịch sử mua hàng:**
```bash
curl -b cookies.txt http://localhost:5001/api/shop/history
```
*Kết quả:*
```json
{
  "success": true,
  "transactions": [
    {
      "item_type": "game_turn",
      "quantity": 5,
      "total_price": 25000,
      "payment_ref": "AMT_1780089184_D2A1C3",
      "status": "paid",
      "created_at": "2026-06-02T20:50:00"
    }
  ]
}
```

---

### Bước 10: Xem bảng xếp hạng và Lịch sử chơi game

**1. Lấy danh sách Top 10 người chơi xuất sắc nhất:**
*(API này công khai, không cần gửi kèm session đăng nhập)*
```bash
curl http://localhost:5001/api/leaderboard
```
*Kết quả:*
```json
{
  "success": true,
  "leaderboard": [
    { "player_name": "Nguyễn Bảo Ngọc", "score": 15, "wins": 1 },
    { "player_name": "Thế Anh", "score": 12, "wins": 0 }
  ]
}
```

**2. Xem lịch sử chơi cá nhân:**
*(Chỉ xem được lịch sử của chính tài khoản đang đăng nhập)*
```bash
curl -b cookies.txt http://localhost:5001/api/game/history
```
*Kết quả:*
```json
{
  "success": true,
  "history": [
    {
      "history_id": 42,
      "result": "Thua ở câu 4 (Hết giờ)",
      "score": 3,
      "duration_sec": 30,
      "played_at": "Tue, 02 Jun 2026 20:44:46 GMT"
    }
  ]
}
```

---

### Bước 11: Các API chẩn đoán và Debug (Dành cho Quản trị viên)
Để hỗ trợ việc kiểm tra lỗi, Server cung cấp một số API chẩn đoán trực quan giúp bạn xem trạng thái kết nối DB, kiểm tra hoạt động của regex hoặc xem nhật ký webhook mà không cần mở trực tiếp PostgreSQL.

**1. Kiểm tra trạng thái hệ thống và kết nối DB:**
```bash
curl http://localhost:5001/api/debug/status
```
*Kết quả trả về:* Trạng thái kết nối DB, 5 giao dịch shop gần nhất, và kết quả kiểm thử Regex xử lý nội dung chuyển khoản tự động.

**2. Xem lịch sử log Webhook nhận được:**
```bash
curl http://localhost:5001/api/debug/webhooks
```
*Kết quả trả về:* Danh sách 20 yêu cầu webhook gần nhất mà hệ thống nhận được từ SePay, hiển thị rõ IP gửi, Payload, thông tin Header, trạng thái xác thực và các lỗi nếu có.

**3. Xem chi tiết vòng đời của 1 mã đơn hàng:**
```bash
curl http://localhost:5001/api/debug/transaction/AMT_1780089184_D2A1C3
```
*Kết quả trả về:* Toàn bộ thông tin liên quan tới đơn hàng, người mua, và ví hiện tại của người mua đó.

---

## 🔒 GIẢI THÍCH CƠ CHẾ XÁC THỰC (AUTHENTICATION) & COOKIE

Tại sao khi dùng trình duyệt ta chỉ cần bấm chuột, còn khi dùng `curl` lại phải thêm `-b cookies.txt` và `-c cookies.txt`?

1. **Flask Session Cookie:**
   - Khi bạn đăng nhập thành công qua `/api/auth/login`, Server Flask sẽ tạo ra một phiên làm việc (Session) lưu trên RAM/Redis của server, đồng thời gửi một Header `Set-Cookie: session=eyJ1c2VyX2lkIjoy...; HttpOnly; Path=/` về cho trình duyệt.
   - Trình duyệt sẽ tự động lưu cookie này lại. Trong tất cả các request tiếp theo gửi lên Server (ví dụ: lấy ví, chơi game, xem lịch sử), trình duyệt sẽ **tự động đính kèm** cookie này ở Header `Cookie`.

2. **Cách curl giả lập trình duyệt:**
   - Tham số `-c cookies.txt` (Cookie Write): Yêu cầu curl ghi lại các cookie mà server trả về (ở bước Login) và lưu vào file `cookies.txt`.
   - Tham số `-b cookies.txt` (Cookie Read): Yêu cầu curl đọc các cookie từ file `cookies.txt` và đính kèm vào HTTP request tiếp theo gửi lên server.
   - Nếu bạn bỏ quên `-b cookies.txt` khi gọi các API cần đăng nhập (như ví dụ ví, cửa hàng, start game), Flask sẽ trả về mã lỗi `401 Unauthorized` hoặc chuyển hướng bạn về trang đăng nhập.
