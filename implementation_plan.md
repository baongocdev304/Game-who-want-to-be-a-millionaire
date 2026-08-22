# Kế hoạch Bổ sung Comment & Docstrings Chi tiết cho Mã nguồn

Yêu cầu của người dùng là **bổ sung comment/docstrings bằng tiếng Việt** cho toàn bộ codebase dự án "Ai Là Triệu Phú" (Bao gồm Backend Python, Database Utilities và Frontend Game Engine).

---

## Các Tệp Sẽ Được Bổ Sung Comment

### 1. Root & Database Utilities
- [app.py](file:///Users/nguyenbaongoc/Documents/millionaire/app.py): File cầu nối WSGI / Render / Docker từ thư mục gốc.
- [database.py](file:///Users/nguyenbaongoc/Documents/millionaire/database.py): Quản lý PostgreSQL Connection Pool, khởi tạo bảng (users, user_passwords, rankings, game_history, user_wallets, shop_transactions, password_reset_codes, webhook_logs), trigger tự động tính tỷ lệ thắng (`win_rate`) và chèn dữ liệu mẫu.
- [update_db.py](file:///Users/nguyenbaongoc/Documents/millionaire/update_db.py): Script cập nhật / migration cơ sở dữ liệu.

### 2. Backend Modules (`backend/`)
- [backend/app.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/app.py): Entry point của ứng dụng Flask backend, nạp tất cả các tuyến route và định tuyến PWA (`manifest.json`, `sw.js`).
- [backend/shared.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/shared.py): Module trung tâm chứa cấu hình Flask app, kết nối Gemini AI API, biến môi trường SePay, hàm kiểm tra đăng nhập (`login_required`), ngân hàng câu hỏi dự phòng cục bộ và hàm sinh câu hỏi AI.
- [backend/register.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/register.py): Xử lý đăng ký tài khoản mới (`/api/auth/register`), mã hóa mật khẩu bcrypt, khởi tạo ví lượt chơi và bảng xếp hạng.
- [backend/login.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/login.py): Xử lý đăng nhập (`/api/auth/login`), kiểm tra session (`/api/auth/me`), và render giao diện.
- [backend/logout.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/logout.py): Xử lý đăng xuất tài khoản (`/api/auth/logout`).
- [backend/forgotpass.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/forgotpass.py) & [mailforgotpass.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/mailforgotpass.py): Xử lý quên mật khẩu, gửi mã xác nhận 6 số qua Email và đổi mật khẩu mới.
- [backend/game_session.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/game_session.py): Khởi tạo phiên chơi mới (`/api/game/start`), trừ lượt chơi, chọn 15 câu hỏi (AI/Fallback) và hàm ghi nhận lịch sử đấu (`record_game_result`).
- [backend/QA.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/QA.py): Xử lý kiểm tra đáp án trả lời (`/api/game/answer`), tính tiền thưởng, mốc quan trọng (Milestone 5, 10, 15).
- [backend/supports.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/supports.py): Logic 3 quyền trợ giúp (50:50, Gọi điện thoại cho người thân, Hỏi ý kiến khán giả).
- [backend/stopped.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/stopped.py): Xử lý khi người chơi chủ động dừng cuộc chơi bảo toàn tiền thưởng (`/api/game/stop`).
- [backend/endtime.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/endtime.py): Xử lý khi hết thời gian trả lời câu hỏi (`/api/game/timeout`).
- [backend/chatbot.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/chatbot.py): Chatbot trợ giúp thông minh sử dụng Gemini AI (`/api/chatbot`).
- [backend/translate.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/translate.py): API dịch thuật hỗ trợ (`/api/translate`).
- [backend/history.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/history.py): Truy xuất lịch sử ván đấu của người chơi (`/api/game/history`).
- [backend/rank.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/rank.py): Truy xuất bảng xếp hạng cao thủ (`/api/leaderboard`).
- [backend/shop.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/shop.py): Cửa hàng vật phẩm, truy xuất ví lượt chơi và khởi tạo đơn hàng nạp tiền SePay QR.
- [backend/bank.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/bank.py): Webhook nhận tín hiệu chuyển khoản tự động từ ngân hàng (SePay) và cộng lượt chơi cho người dùng.
- [backend/debug.py](file:///Users/nguyenbaongoc/Documents/millionaire/backend/debug.py): API kiểm tra trạng thái hệ thống và nhật ký webhook.

### 3. Frontend Logic
- [static/js/game.js](file:///Users/nguyenbaongoc/Documents/millionaire/static/js/game.js): Toàn bộ logic frontend (Quản lý trạng thái game, bộ đếm thời gian, âm thanh, hiệu ứng UI, gọi API backend).

---

## Kế hoạch Kiểm tra & Xác minh (Verification Plan)

### Automated Checks
- Chạy lệnh kiểm tra cú pháp Python: `python3 -m py_compile backend/*.py app.py database.py update_db.py` để đảm bảo việc thêm comment không làm hỏng cú pháp code.
- Chạy lệnh thử nghiệm ứng dụng Flask ở chế độ check config / unit test cơ bản để chắc chắn server import hoàn toàn bình thường.
