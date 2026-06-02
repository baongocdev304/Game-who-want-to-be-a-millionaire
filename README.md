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
```

---

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
