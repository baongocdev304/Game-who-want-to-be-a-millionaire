# 📅 Kế Hoạch Học Code Backend — Dự Án "Ai Là Triệu Phú"

> **Thời gian:** 25/08/2026 → 30/09/2026 (6 tuần, 38 buổi)  
> **Mục tiêu:** Hiểu rõ và tự code lại toàn bộ dự án từ đầu  
> **Ngôn ngữ:** Python (Flask) + PostgreSQL + Google Gemini AI

---

## 🏗️ Kiến trúc hệ thống (4 tầng)

```
┌────────────────────────────────────────────────────┐
│  Tầng 1: Cấu hình & Database                       │
│  .env              database.py                     │
└────────────────────────┬───────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────┐
│  Tầng 2: Module Trung Tâm                           │
│  backend/shared.py                                 │
└────────────────────────┬───────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────┐
│  Tầng 3: Các File Chức Năng (Route Modules)         │
│  register.py  login.py  logout.py  forgotpass.py   │
│  game_session.py  QA.py  supports.py  stopped.py   │
│  endtime.py  chatbot.py  translate.py  history.py  │
│  rank.py  shop.py  bank.py  debug.py               │
└────────────────────────┬───────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────┐
│  Tầng 4: Entry Point - Khởi Chạy Server             │
│  backend/app.py  →  app.py (root WSGI)             │
└────────────────────────────────────────────────────┘
```

---

## Tuần 1 (25/08 → 31/08): Nền tảng & Xác thực Tài khoản

> **Mục tiêu:** Dựng xong 4 tầng kiến trúc cơ bản, hoàn thành luồng Đăng ký + Đăng nhập.

| Buổi | Nội dung | File | Kết quả |
|:---:|:---|:---|:---|
| 1 | Setup `.env`. Viết `database.py`: ConnectionPool, `get_connection()`, `release_connection()`, `create_schema()` | `.env`, `database.py` | `python database.py` → `✅ Tạo schema thành công!` |
| 2 | `shared.py` phần 1: Khởi tạo Flask app, `secret_key`, CORS. Viết `get_db()` + `close_db()` (dùng `g` object) | `backend/shared.py` | Flask app chạy được, `get_db()` trả về connection |
| 3 | `shared.py` phần 2: Viết `hash_password()`, `check_password()` (bcrypt). Viết decorator `@login_required`. Ôn `try/except` | `backend/shared.py` | Test mã hóa password OK |
| 4 | Code `register.py`: Route `/api/auth/register`, validate input, xử lý trùng username/email | `backend/register.py` | POST Postman → `{ "success": true }` |
| 5 | Code `login.py`: `/api/auth/login`, `/api/auth/me`, `/`, `/auth` | `backend/login.py` | Login thành công, `/api/auth/me` → `logged_in: true` |
| 6 | Viết `app.py` entry point, import routes, gọi `create_schema`. Test flow end-to-end | `backend/app.py` | Flow Register → Login → Me hoàn chỉnh |
| 7 | Ôn SQL queries (`SELECT`, `INSERT`, `JOIN`). Debug lỗi. Review kiến trúc 4 tầng | Tất cả | Nắm vững SQL, hiểu rõ 4 tầng |

---

## Tuần 2 (01/09 → 07/09): Hoàn thiện Auth & Khởi động Game

> **Mục tiêu:** Hoàn thành logout, quên mật khẩu. Bắt đầu tính năng khởi tạo ván chơi.

| Buổi | Nội dung | File | Kết quả |
|:---:|:---|:---|:---|
| 8 | Code `logout.py`: `session.clear()`. Test Login → Logout → `/api/auth/me` | `backend/logout.py` | Logout xóa sạch session |
| 9 | `shared.py` phần email: cấu hình SMTP, viết `send_email_code()` | `backend/shared.py` | Gửi mã 6 số qua console OK |
| 10 | `forgotpass.py` Bước 1: Route `/api/auth/forgot-password`, tạo mã 6 số, lưu DB, gửi email | `backend/forgotpass.py` | Postman → Mã 6 số được tạo và lưu DB |
| 11 | `forgotpass.py` Bước 2: Route `/api/auth/verify-reset-code`, kiểm tra mã, đổi mật khẩu | `backend/forgotpass.py` | Flow quên MK hoàn chỉnh |
| 12 | `shared.py` - Constants: `PRIZE_LEVELS`, `MILESTONES`, `get_or_create_wallet()` | `backend/shared.py` | Hiểu bảng `user_wallets` |
| 13 | `game_session.py` - `start_game()`: kiểm tra lượt, sinh câu hỏi, tạo phiên | `backend/game_session.py` | Postman → Nhận câu hỏi đầu tiên |
| 14 | `game_session.py` - `record_game_result()`: INSERT `game_history`, UPDATE `rankings` | `backend/game_session.py` | Ghi lịch sử vào DB thành công |

---

## Tuần 3 (08/09 → 14/09): Logic Game Chính

> **Mục tiêu:** Code xong toàn bộ logic lõi — Trả lời đáp án, 3 quyền trợ giúp, dừng, hết giờ.

| Buổi | Nội dung | File | Kết quả |
|:---:|:---|:---|:---|
| 15 | `QA.py` phần 1: Route `/api/game/answer`, xử lý trả lời **đúng** | `backend/QA.py` | Chọn đáp án đúng → Nhận câu tiếp |
| 16 | `QA.py` phần 2: Xử lý trả lời **sai** (mốc an toàn) + **thắng câu 15** | `backend/QA.py` | Sai → mốc an toàn. Thắng → `is_winner: true` |
| 17 | `supports.py` phần 1: Quyền **50:50** (loại 2 đáp án sai) | `backend/supports.py` | 50:50 → Chỉ còn 2 đáp án |
| 18 | `supports.py` phần 2: **Gọi ĐT** (AI gợi ý) + **Hỏi khán giả** (% bình chọn) | `backend/supports.py` | Phone → AI gợi ý. Audience → Biểu đồ % |
| 19 | `stopped.py`: Route `/api/game/stop`, bảo toàn tiền thưởng | `backend/stopped.py` | Stop → Nhận đúng tiền thưởng hiện tại |
| 20 | `endtime.py`: Route `/api/game/timeout`, xử lý hết 30 giây | `backend/endtime.py` | Timeout → Kết quả thua + mốc an toàn |
| 21 | **Test toàn diện:** Chơi 1 ván hoàn chỉnh qua Postman | Tất cả | 1 ván game hoàn chỉnh không lỗi |

---

## Tuần 4 (15/09 → 21/09): Tích hợp AI (Google Gemini)

> **Mục tiêu:** Kết nối Gemini AI sinh câu hỏi, xây chatbot MC, API dịch thuật.

| Buổi | Nội dung | File | Kết quả |
|:---:|:---|:---|:---|
| 22 | Tìm hiểu Gemini API: lấy key, cài `google-genai`, test gọi AI | `backend/shared.py` | Script gọi Gemini → Nhận text |
| 23 | Hàm `generate_questions_with_ai()`: Prompt 15 câu hỏi, parse JSON | `backend/shared.py` | Mảng 15 câu hỏi JSON hợp lệ |
| 24 | Ngân hàng câu hỏi offline + `get_local_fallback_questions()` | `backend/shared.py` | 15 câu offline với đáp án xáo trộn |
| 25 | Tích hợp AI vào `game_session.py`: AI chính, offline dự phòng | `backend/game_session.py` | Start game → Ưu tiên AI, fallback offline |
| 26 | `chatbot.py`: Route `/api/chatbot`, prompt MC Trợ Lý, không lộ đáp án | `backend/chatbot.py` | Gửi tin nhắn → AI trả lời đúng giọng MC |
| 27 | `translate.py`: Route `/api/translate`, dịch câu hỏi qua Gemini | `backend/translate.py` | Tiếng Việt → Bản dịch tiếng Anh |
| 28 | **Test toàn diện AI:** Start bằng AI → Chơi → Chat MC → Dịch | Tất cả | Toàn bộ tính năng AI hoạt động |

---

## Tuần 5 (22/09 → 28/09): Cửa hàng, Thanh toán & Dữ liệu

> **Mục tiêu:** Hệ thống cửa hàng, webhook ngân hàng SePay, lịch sử & xếp hạng.

| Buổi | Nội dung | File | Kết quả |
|:---:|:---|:---|:---|
| 29 | `history.py`: Route `/api/game/history`, `ORDER BY`, `LIMIT` | `backend/history.py` | GET → Danh sách lịch sử ván đấu |
| 30 | `rank.py`: Route `/api/leaderboard`, `JOIN`, `ORDER BY DESC` | `backend/rank.py` | GET → Bảng xếp hạng top 20 |
| 31 | `shop.py` phần 1: `/api/shop/wallet`, cấu hình SePay | `backend/shop.py` | GET wallet → `{ game_turns: 3 }` |
| 32 | `shop.py` phần 2: `/api/shop/create-order`, sinh VietQR URL | `backend/shop.py` | POST → QR URL + payment_ref |
| 33 | `bank.py` phần 1: `/api/shop/webhook`, xác thực Signature | `backend/bank.py` | Webhook giả → Xác thực thành công |
| 34 | `bank.py` phần 2: Bóc tách `payment_ref`, cộng lượt chơi | `backend/bank.py` | Webhook → Ví tự cộng lượt chơi |
| 35 | `debug.py` + Test toàn diện: flow Mua lượt → Webhook → Ví | `backend/debug.py` | Flow thanh toán end-to-end OK |

---

## Tuần 6 (29/09 → 30/09): Frontend, DevOps & Tổng kết

> **Mục tiêu:** Hiểu Frontend, Docker, Deploy lên Render.

| Buổi | Nội dung | File | Kết quả |
|:---:|:---|:---|:---|
| 36 | Đọc hiểu `game.js`: Phân tích hàm JS ↔ API Backend | `static/js/game.js` | Hiểu cách Frontend giao tiếp Backend |
| 37 | Đọc hiểu HTML Templates + PWA (`manifest.json`, `sw.js`) | `templates/*.html` | Hiểu luồng HTML ↔ JS ↔ API |
| 38 | Docker + Deploy: `Dockerfile`, `docker-compose.yml`, `Procfile`. Tổng kết dự án, viết README | `Dockerfile`, `Procfile` | Hiểu Docker/Deploy, README hoàn chỉnh |

---

## 📊 Danh sách API Endpoints

| # | Method | Endpoint | File Backend | Mô tả |
|:---:|:---:|:---|:---|:---|
| 1 | POST | `/api/auth/register` | `register.py` | Đăng ký tài khoản |
| 2 | POST | `/api/auth/login` | `login.py` | Đăng nhập |
| 3 | GET | `/api/auth/me` | `login.py` | Kiểm tra trạng thái đăng nhập |
| 4 | POST | `/api/auth/logout` | `logout.py` | Đăng xuất |
| 5 | POST | `/api/auth/forgot-password` | `forgotpass.py` | Gửi mã khôi phục |
| 6 | POST | `/api/auth/verify-reset-code` | `forgotpass.py` | Xác nhận mã & đổi mật khẩu |
| 7 | POST | `/api/game/start` | `game_session.py` | Bắt đầu ván chơi mới |
| 8 | POST | `/api/game/answer` | `QA.py` | Chốt đáp án câu hỏi |
| 9 | POST | `/api/game/lifeline` | `supports.py` | Sử dụng quyền trợ giúp |
| 10 | POST | `/api/game/stop` | `stopped.py` | Dừng cuộc chơi bảo toàn tiền |
| 11 | POST | `/api/game/timeout` | `endtime.py` | Hết thời gian trả lời |
| 12 | GET | `/api/game/history` | `history.py` | Lịch sử ván đấu |
| 13 | GET | `/api/leaderboard` | `rank.py` | Bảng xếp hạng |
| 14 | POST | `/api/chatbot` | `chatbot.py` | Chat với MC Trợ Lý AI |
| 15 | POST | `/api/translate` | `translate.py` | Dịch câu hỏi |
| 16 | GET | `/api/shop/wallet` | `shop.py` | Xem ví lượt chơi |
| 17 | POST | `/api/shop/create-order` | `shop.py` | Tạo đơn mua lượt |
| 18 | POST | `/api/shop/webhook` | `bank.py` | Webhook nhận chuyển khoản |
| 19 | GET | `/api/debug/status` | `debug.py` | Kiểm tra trạng thái hệ thống |

---

## ✅ Checklist Kiến thức

- [ ] **Python:** `try/except`, `if/else`, `for`, `with`, `import`, `decorator`
- [ ] **Flask:** Route, Request, Response, Session, `g` object, `teardown_appcontext`
- [ ] **PostgreSQL:** `SELECT`, `INSERT`, `UPDATE`, `JOIN`, `ON CONFLICT`, Connection Pool
- [ ] **Bảo mật:** bcrypt hash, `.env`, `.gitignore`, Webhook authentication
- [ ] **API Design:** RESTful endpoints, JSON, Postman testing
- [ ] **AI:** Google Gemini API, Prompt Engineering
- [ ] **Payment:** SePay webhook, VietQR
- [ ] **DevOps:** Docker, docker-compose, Procfile, Deploy Render
