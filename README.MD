# 🏆 GAME "AI LÀ TRIỆU PHÚ" - FULLSTACK WEB & AI ENGINE

> **Dự án Game Trắc Nghiệm Trực Tuyến "Ai Là Triệu Phú"** được xây dựng bằng **Python (Flask)**, kết hợp công nghệ **Google Gemini AI** để sinh câu hỏi động & đóng vai MC trợ lý, tích hợp nạp tiền tự động qua **SePay Webhook**, cơ sở dữ liệu **PostgreSQL** và hỗ trợ **PWA (Progressive Web App)**.

---

## 📋 MỤC LỤC
1. [Tổng Quan Architecture & Công Nghệ](#-tổng-quan-architecture--công-nghệ)
2. [Cấu Trúc Thư Mục Backend Modular](#-cấu-trúc-thư-mục-backend-modular)
3. [Luồng Hoạt Động Chi Tiết (Execution Flows)](#-luồng-hoạt-động-chi-tiết-execution-flows)
   - [3.1. Luồng Khởi Chạy Server & Tầng Shared Module](#31-luồng-khởi-chạy-server--tầng-shared-module)
   - [3.2. Luồng Xắc Thực (Authentication & Session)](#32-luồng-xác-thực-authentication--session)
   - [3.3. Luồng Chơi Game & Gemini AI Sinh Câu Hỏi](#33-luồng-chơi-game--gemini-ai-sinh-câu-hỏi)
   - [3.4. Luồng Xử Lý Trả Lời & 3 Quyền Trợ Giúp](#34-luồng-xử-lý-trả-lời--3-quyền-trợ-giúp)
   - [3.5. Luồng Thanh Toán & Webhook Tự Động (SePay)](#35-luồng-thanh-toán--webhook-tự-động-sepay)
   - [3.6. Luồng MC Trợ Lý Chatbot (Gemini AI Persona)](#36-luồng-mc-trợ-lý-chatbot-gemini-ai-persona)
4. [Cơ Sở Dữ Liệu PostgreSQL (Schema & Trigger)](#-cơ-sở-dữ-liệu-postgresql-schema--trigger)
5. [Danh Sách Tất Cả 28 API Endpoints](#-danh-sách-tất-cả-28-api-endpoints)
6. [Hướng Dẫn Cài Đặt & Chạy Local](#-hướng-dẫn-cài-đặt--chạy-local)
7. [Hướng Dẫn Deploy Lên Render.com](#-hướng-dẫn-deploy-lên-rendercom)

---

## 🔌 TỔNG QUAN ARCHITECTURE & CÔNG NGHỆ

```
┌────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND / CLIENT                             │
│       HTML5 / Vanilla CSS3 / JavaScript (ES6+) / Web Audio API        │
│                PWA Support (manifest.json, sw.js)                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST API (JSON)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          FLASK BACKEND SERVER                          │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │               app.py (Entry Point / Router Register)           │   │
│   └───────────────────────────────┬────────────────────────────────┘   │
│                                   ▼                                    │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │            shared.py (Central Shared State & Services)         │   │
│   └────────┬──────────────────────┬──────────────────────┬─────────┘   │
│            │                      │                      │             │
│            ▼                      ▼                      ▼             │
│   ┌────────────────┐     ┌────────────────┐     ┌────────────────┐     │
│   │ Auth Modules   │     │ Game Logic     │     │ Shop / Payment │     │
│   │ (login, reg...)│     │ (QA, sess...)  │     │ (bank, shop)   │     │
│   └────────────────┘     └────────────────┘     └────────────────┘     │
└────────────┬──────────────────────┬──────────────────────┬─────────────┘
             │                      │                      │
             ▼                      ▼                      ▼
┌────────────────────────┐ ┌──────────────────┐ ┌────────────────────────┐
│      POSTGRESQL        │ │  GOOGLE GEMINI   │ │     SEPAY WEBHOOK      │
│ Connection Pool (psycopg2)│ │ AI Engine Flash  │ │  Auto Payment Gateway  │
└────────────────────────┘ └──────────────────┘ └────────────────────────┘
```

### 🛠 Tech Stack Chi Tiết:
* **Backend Framework:** Python 3.11+ / Flask / Flask-CORS.
* **Database:** PostgreSQL với Pool kết nối (`psycopg2.pool.SimpleConnectionPool`).
* **AI Integration:** Google GenAI SDK (`google-genai`), Model: `gemini-flash-latest`.
* **Security & Auth:** `bcrypt` (băm mật khẩu an toàn), Flask Session (Cookie Mã Hóa).
* **Payment Integration:** SePay API Webhook + QR Code ngân hàng tự động.
* **Email Gateway:** Python `smtplib` + `email.mime` (Gửi OTP khôi phục mật khẩu).
* **Frontend UI/UX:** Responsive Glassmorphism Design, hiệu ứng âm thanh sống động (Web Audio API), Progressive Web App (PWA).

---

## 📁 CẤU TRÚC THƯ MỤC BACKEND MODULAR

Dự án áp dụng **Mô hình 3 Tầng Tránh Circular Import (Shared-Centric Architecture)**:

```
millionaire/
├── database.py              # Schema DB, Trigger win_rate, Connection Pool
├── backend/
│   ├── app.py               # 🚀 Entry Point duy nhất (Import tất cả routes)
│   ├── shared.py            # 🔧 Shared Module (Flask App, Config, DB Utils, Helpers)
│   ├── register.py          # 🔐 Route: Đăng ký tài khoản
│   ├── login.py             # 🔐 Route: Đăng nhập, Check Session, Trang chủ
│   ├── logout.py            # 🔐 Route: Đăng xuất
│   ├── forgotpass.py        # 🔐 Route: Quên mật khẩu & xác nhận mã OTP
│   ├── mailforgotpass.py    # 📧 Service: Gửi Email OTP
│   ├── game_session.py      # 🎮 Route: Khởi tạo phiên chơi mới & lưu kết quả
│   ├── QA.py                # 🎮 Route: Xử lý trả lời & Generator câu hỏi Gemini AI
│   ├── supports.py          # 🎮 Route: 3 Quyền trợ giúp (50:50, Gọi ĐT, Khán giả)
│   ├── stopped.py           # 🎮 Route: Dừng cuộc chơi chủ động
│   ├── endtime.py           # 🎮 Route: Hết giờ suy nghĩ (30s)
│   ├── chatbot.py           # 🤖 Route: MC Trợ Lý AI Chatbot
│   ├── translate.py         # 🌐 Route: Dịch câu hỏi AI
│   ├── history.py           # 📊 Route: Lịch sử đấu của người chơi
│   ├── rank.py              # 🏆 Route: Bảng xếp hạng cao thủ
│   ├── shop.py              # 🛒 Route: Cửa hàng & Tạo đơn mua lượt/trợ giúp
│   ├── bank.py              # 💳 Route: Webhook nhận tiền từ SePay
│   └── debug.py             # 🔍 Route: Debug & kiểm tra hệ thống
├── templates/               # Các trang HTML (index.html, signin.html, shop.html...)
├── static/                  # CSS, JS, âm thanh, hình ảnh, PWA sw.js, manifest.json
└── .env                     # Chứa biến môi trường (KHÔNG PUSH GIT)
```

---

## 🔄 LUỒNG HOẠT ĐỘNG CHI TIẾT (EXECUTION FLOWS)

### 3.1. Luồng Khởi Chạy Server & Tầng Shared Module
```mermaid
sequenceDiagram
    autonumber
    participant App as backend/app.py
    participant Shared as backend/shared.py
    participant DB as database.py
    participant Route as Route Modules (register, QA...)

    App->>Shared: Import app, get_connection, create_schema
    Note over Shared: 1. Load .env<br/>2. Init Gemini Client<br/>3. Init Flask(app) & CORS<br/>4. Init Constants & Utils
    App->>DB: get_connection() & create_schema(conn)
    Note over DB: Tạo bảng (users, user_wallets, game_history...)<br/>Tạo Indexes & Trigger win_rate
    App->>Route: Import từng route module ở cuối file app.py
    Note over Route: Mỗi route import (app, get_db...) từ shared.py<br/>Đăng ký decorator @app.route
    App->>App: app.run(host='0.0.0.0', port=5002)
```

---

### 3.2. Luồng Xác Thực (Authentication & Session)
```mermaid
sequenceDiagram
    autonumber
    participant Client as Browser / Postman
    participant Auth as login.py / register.py
    participant Shared as shared.py
    participant DB as PostgreSQL

    Client->>Auth: POST /api/auth/register {username, password, email, display_name}
    Auth->>Shared: get_db()
    Auth->>DB: Check username/email đã tồn tại chưa
    alt Đã tồn tại
        Auth-->>Client: 400 Bad Request ("Tên đăng nhập đã tồn tại")
    else Hợp lệ
        Auth->>Shared: hash_password(password) (bcrypt)
        Auth->>DB: INSERT INTO users ... (Commit DB)
        Auth->>DB: INSERT INTO user_wallets (Cấp 3 lượt chơi mặc định)
        Auth-->>Client: 200 OK ("Đăng ký thành công")
    end

    Client->>Auth: POST /api/auth/login {username, password}
    Auth->>DB: SELECT * FROM users WHERE username = %s
    Auth->>Shared: check_password(password, hashed_pw)
    alt Đúng mật khẩu
        Auth->>Auth: Lưu session['username'], session['user_id']
        Auth-->>Client: 200 OK {success: true, redirect: '/'}
    else Sai mật khẩu
        Auth-->>Client: 401 Unauthorized ("Mật khẩu không chính xác")
    end
```

---

### 3.3. Luồng Chơi Game & Gemini AI Sinh Câu Hỏi
```mermaid
sequenceDiagram
    autonumber
    participant Client as Game Client (JS)
    participant Sess as game_session.py
    participant QA as QA.py (AI Engine)
    participant Gemini as Google Gemini AI
    participant DB as PostgreSQL

    Client->>Sess: POST /api/game/start
    Sess->>DB: SELECT game_turns FROM user_wallets WHERE user_id = %s
    alt Số lượt chơi <= 0
        Sess-->>Client: 400 Bad Request ("Hết lượt chơi! Vui lòng vào Shop nạp thêm")
    else Còn lượt chơi
        Sess->>DB: UPDATE user_wallets SET game_turns = game_turns - 1
        Sess->>QA: generate_questions_with_ai()
        
        rect rgb(235, 245, 255)
            Note over QA,Gemini: Luồng Sinh Câu Hỏi Động
            QA->>Gemini: Call gemini_client.models.generate_content(prompt)
            Note over Gemini: Sáng tác 15 câu hỏi thuần Việt:<br/>- Câu 1-5: Dễ (Easy)<br/>- Câu 6-10: Trung bình (Medium)<br/>- Câu 11-15: Khó (Hard)
            Gemini-->>QA: JSON String 15 câu hỏi
            alt Gemini thành công
                QA-->>Sess: Mảng 15 câu hỏi AI
            else Gemini mất mạng / lỗi API Key
                QA->>QA: get_local_fallback_questions() (Lấy bộ câu hỏi thuần Việt cục bộ)
                QA-->>Sess: Mảng 15 câu hỏi dự phòng
            end
        end

        Sess->>Sess: Tạo session_id (UUID), lưu vào RAM `sessions[session_id]`
        Sess-->>Client: 200 OK {session_id, question_1, prize_levels}
    end
```

---

### 3.4. Luồng Xử Lý Trả Lời & 3 Quyền Trợ Giúp
```mermaid
sequenceDiagram
    autonumber
    participant Client as Game Client (JS)
    participant QA as QA.py
    participant Sup as supports.py
    participant DB as PostgreSQL

    rect rgb(240, 255, 240)
        Note over Client,QA: Trả Lời Câu Hỏi
        Client->>QA: POST /api/game/answer {session_id, answer_index}
        QA->>QA: Lấy phiên chơi từ RAM `sessions[session_id]`
        alt Trả lời ĐÚNG
            QA->>QA: Tăng current_question + 1, Cập nhật tiền thưởng
            alt Đạt câu 15 (THẮNG GAME)
                QA->>DB: record_game_result(user_id, 'win', 150.000.000, total_time)
                QA-->>Client: {is_correct: true, game_over: true, won: true, prize: "150.000.000 đ"}
            else Chưa hết 15 câu
                QA-->>Client: {is_correct: true, game_over: false, next_question}
            end
        else Trả lời SAI
            QA->>QA: Tính mốc an toàn (Câu 5: 2tr, Câu 10: 22tr)
            QA->>DB: record_game_result(user_id, 'loss', safe_prize, total_time)
            QA-->>Client: {is_correct: false, game_over: true, won: false, prize: safe_prize}
        end
    end

    rect rgb(255, 250, 240)
        Note over Client,Sup: Dùng Quyền Trợ Giúp
        Client->>Sup: POST /api/game/lifeline {session_id, type: "50:50" | "phone" | "audience"}
        Sup->>Sup: Kiểm tra quyền này đã dùng trong phiên chưa
        alt 50:50
            Sup->>Sup: Bỏ 2 đáp án sai ngẫu nhiên
            Sup-->>Client: {removed_answers: [0, 2]}
        alt Gọi điện người thân
            Sup->>Sup: AI giả lập người thân chọn đáp án (xác suất 70-80% đúng)
            Sup-->>Client: {suggestion: "Tôi nghĩ đáp án B là chính xác!"}
        alt Hỏi ý kiến khán giả
            Sup->>Sup: Tính % bình chọn khán giả trường quay (dựa theo độ khó)
            Sup-->>Client: {poll: {A: 10%, B: 75%, C: 10%, D: 5%}}
        end
    end
```

---

### 3.5. Luồng Thanh Toán & Webhook Tự Động (SePay)
```mermaid
sequenceDiagram
    autonumber
    participant User as Người chơi
    participant Shop as shop.py
    participant Bank as bank.py
    participant SePay as SePay Gateway / Ngân Hàng
    participant DB as PostgreSQL

    User->>Shop: POST /api/shop/create-order {pack_id: "pack_5_turns"}
    Shop->>Shop: Tạo mã giao dịch tham chiếu reference_code (VD: "ALT123456")
    Shop-->>User: Trả về QR Code VietQR (MBBank/TPBank) chứa cú pháp "ALT123456"

    User->>SePay: Chuyển khoản ngân hàng quét mã QR
    SePay->>Bank: POST /api/shop/webhook (Hoặc /api/webhook/sepay) với Header Authorization: Bearer WEBHOOK_SECRET
    
    Bank->>Bank: Xử lý Clean Envs & Kiểm tra Authenticate WEBHOOK_SECRET
    alt Secret Sai
        Bank-->>SePay: 401 Unauthorized
    else Secret Đúng
        Bank->>Bank: Trích xuất content chuyển khoản chứa mã "ALT123456"
        Bank->>DB: SELECT user_id FROM transactions WHERE reference_code = 'ALT123456'
        Bank->>DB: UPDATE transactions SET status = 'completed'
        Bank->>DB: UPDATE user_wallets SET game_turns = game_turns + 5 (Cộng 5 lượt chơi)
        Bank->>DB: COMMIT TRANSACTION
        Bank-->>SePay: 200 OK {success: true}
    end

    Note over User,Shop: Frontend Polling /api/shop/check-status?ref=ALT123456 -> Nhận thông báo nạp thành công!
```

---

### 3.6. Luồng MC Trợ Lý Chatbot (Gemini AI Persona)
```mermaid
sequenceDiagram
    autonumber
    participant Client as Chat Widget Frontend
    participant Chat as chatbot.py
    participant Shared as shared.py (Gemini Engine)
    participant Gemini as Google Gemini AI

    Client->>Chat: POST /api/chatbot {message: "Câu này khó quá làm sao đây?", session_id}
    Chat->>Shared: Lấy trạng thái phiên chơi hiện tại (Tên người chơi, Câu hỏi số mấy)
    Chat->>Chat: Xây dựng System Prompt đóng vai MC Trợ Lý:
    Note over Chat: - Persona: MC Lại Văn Sâm / Đinh Tiến Dũng vui vẻ, động viên<br/>- Constraint: KHÔNG ĐƯỢC LỘ ĐÁP ÁN ĐÚNG<br/>- Ngắn gọn < 3 câu
    Chat->>Gemini: gemini_client.models.generate_content(prompt)
    Gemini-->>Chat: "Chào bạn! Câu số 8 này quả thực là thử thách lớn. Đừng ngần ngại dùng quyền trợ giúp 50:50 nhé!"
    Chat-->>Client: 200 OK {success: true, reply: "..."}
```

---

## 🗄️ CƠ SỞ DỮ LIỆU POSTGRESQL (SCHEMA & TRIGGER)

Khởi tạo tự động thông qua `database.py`:

```sql
-- 1. Bảng người dùng
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng ví lượt chơi & trợ giúp
CREATE TABLE IF NOT EXISTS user_wallets (
    wallet_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    game_turns INT DEFAULT 3,
    bonus_lifelines INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Bảng lịch sử đấu
CREATE TABLE IF NOT EXISTS game_history (
    history_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    result VARCHAR(10) CHECK (result IN ('win', 'loss', 'stopped')),
    score BIGINT DEFAULT 0,
    correct_count INT DEFAULT 0,
    total_time_seconds INT DEFAULT 0,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Bảng giao dịch nạp tiền SePay
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    reference_code VARCHAR(50) UNIQUE NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    item_type VARCHAR(20) CHECK (item_type IN ('turns', 'lifelines')),
    item_quantity INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 5. Trigger tự động tính tỷ lệ thắng (Win Rate)
CREATE OR REPLACE FUNCTION update_user_win_rate() RETURNS TRIGGER AS $$
BEGIN
    -- Đã tích hợp sẵn trong schema database.py
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

## 🔌 DANH SÁCH TẤT CẢ 28 API ENDPOINTS

| STT | Endpoint | Method | Module | Mô Tả |
|---|---|---|---|---|
| 1 | `/` | GET | `login.py` | Trang chơi game chính (Yêu cầu đăng nhập) |
| 2 | `/auth` | GET | `login.py` | Trang Đăng nhập / Đăng ký HTML |
| 3 | `/api/auth/register` | POST | `register.py` | Đăng ký tài khoản người dùng mới |
| 4 | `/api/auth/login` | POST | `login.py` | Đăng nhập tài khoản |
| 5 | `/api/auth/logout` | POST | `logout.py` | Đăng xuất phiên làm việc |
| 6 | `/api/auth/me` | GET | `login.py` | Lấy thông tin user hiện tại từ session |
| 7 | `/api/auth/forgot-password` | POST | `forgotpass.py` | Yêu cầu gửi mã OTP khôi phục mật khẩu |
| 8 | `/api/auth/verify-reset-code` | POST | `forgotpass.py` | Xác nhận mã OTP & đổi mật khẩu mới |
| 9 | `/api/game/start` | POST | `game_session.py` | Trừ lượt & Khởi tạo phiên chơi (Sinh câu hỏi AI) |
| 10 | `/api/game/answer` | POST | `QA.py` | Kiểm tra đáp án câu hỏi |
| 11 | `/api/game/lifeline` | POST | `supports.py` | Trợ giúp: 50:50, Gọi điện, Khán giả |
| 12 | `/api/game/stop` | POST | `stopped.py` | Dừng cuộc chơi chủ động nhận tiền thưởng |
| 13 | `/api/game/timeout` | POST | `endtime.py` | Xử lý khi hết 30 giây suy nghĩ |
| 14 | `/api/game/history` | GET | `history.py` | Lấy lịch sử các ván đấu của user |
| 15 | `/api/leaderboard` | GET | `rank.py` | Bảng xếp hạng cao thủ điểm cao |
| 16 | `/api/chatbot` | POST | `chatbot.py` | Chat với MC Trợ Lý AI (Gemini) |
| 17 | `/api/translate` | POST | `translate.py` | Dịch thuật câu hỏi bằng AI |
| 18 | `/api/shop/wallet` | GET | `shop.py` | Kiểm tra số dư lượt chơi hiện có |
| 19 | `/api/shop/create-order` | POST | `shop.py` | Tạo đơn hàng nạp lượt chơi (Trả về VietQR) |
| 20 | `/api/shop/check-status` | GET | `shop.py` | Kiểm tra trạng thái đơn nạp |
| 21 | `/api/shop/history` | GET | `shop.py` | Xem lịch sử nạp tiền |
| 22 | `/api/shop/webhook` | POST | `bank.py` | Webhook nhận callback tự động từ SePay |
| 23 | `/api/webhook/sepay` | POST | `bank.py` | Alias endpoint cho SePay Webhook |
| 24 | `/api/debug/status` | GET | `debug.py` | Debug kiểm tra thông số hệ thống |
| 25 | `/api/debug/webhooks` | GET | `debug.py` | Xem log webhook nhận được |
| 26 | `/api/debug/transaction/<ref>` | GET | `debug.py` | Kiểm tra thông tin 1 mã giao dịch |
| 27 | `/manifest.json` | GET | `app.py` | Trả về file manifest PWA |
| 28 | `/sw.js` | GET | `app.py` | Trả về Service Worker PWA |

---

## 🛠 HƯỚNG DẪN CÀI ĐẶT & CHẠY LOCAL

### 1. Yêu cầu hệ thống
* Python 3.11+
* PostgreSQL Database Server (hoặc Docker PostgreSQL)

### 2. Tạo Môi Trường Ảo & Cài Đặt Dependencies
```bash
# Clone dự án
git clone https://github.com/baongocdev304/Game-who-want-to-be-a-millionaire.git
cd Game-who-want-to-be-a-millionaire

# Tạo & kích hoạt virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Cài đặt các thư viện cần thiết
pip install flask flask-cors python-dotenv bcrypt psycopg2-binary google-genai
```

### 3. Cấu Hình File `.env`
Tạo file `.env` tại thư mục gốc dự án:
```env
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/millionaire_db

# Flask Secret Key
SECRET_KEY=millionaire-secret-key-2026

# Google Gemini AI Key
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere

# SePay Payment Configuration
SEPAY_BANK_CODE=MBBank
SEPAY_ACCOUNT_NO=0123456789
SEPAY_ACCOUNT_NAME=AI LA TRIEU PHU
WEBHOOK_SECRET=your-webhook-secret-key

# Email Support (Optional for Forgot Password)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_SENDER=Ai Là Triệu Phú Support <support@millionaire.com>
```

### 4. Khởi Chạy Server
```bash
cd backend
python3 app.py
```
TRUY CẬP TRÌNH DUYỆT: **`http://localhost:5002`**

---

## 🚀 HƯỚNG DẪN DEPLOY LÊN RENDER.COM

### Step 1: Tạo PostgreSQL Database trên Render
1. Đăng nhập [Render Dashboard](https://dashboard.render.com/).
2. Chọn **New +** ➔ **PostgreSQL**.
3. Điền tên DB và chọn Free Tier.
4. Sau khi tạo xong, copy chuỗi **Internal Database URL** hoặc **External Database URL**.

### Step 2: Tạo Web Service
1. Chọn **New +** ➔ **Web Service**.
2. Kết nối với Repository GitHub của bạn.
3. Cấu hình thông số:
   * **Runtime:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt` (Hoặc `pip install flask flask-cors python-dotenv bcrypt psycopg2-binary google-genai gunicorn`)
   * **Start Command:** `cd backend && gunicorn app:app`
4. Trong phần **Environment Variables**, thêm đầy đủ các biến:
   * `DATABASE_URL` (dán URL PostgreSQL của Render ở Step 1)
   * `GEMINI_API_KEY`
   * `SECRET_KEY`
   * `WEBHOOK_SECRET`
   * `SEPAY_ACCOUNT_NO`, `SEPAY_ACCOUNT_NAME`, `SEPAY_BANK_CODE`

### Step 3: Tích Hợp Webhook SePay (Nếu Có)
1. Đăng nhập cấu hình Webhook trên SePay.
2. Điền URL Callback: `https://<ten-app-render>.onrender.com/api/shop/webhook`
3. Điền **Authentication Token** trùng với `WEBHOOK_SECRET` trong biến môi trường.

---

## 📝 LICENSE & AUTHOR
* **Tác giả:** Nguyễn Bảo Ngọc
* **Repository:** [baongocdev304/Game-who-want-to-be-a-millionaire](https://github.com/baongocdev304/Game-who-want-to-be-a-millionaire)
* **Phiên bản:** v3.0.0 Modular AI Edition (2026)
