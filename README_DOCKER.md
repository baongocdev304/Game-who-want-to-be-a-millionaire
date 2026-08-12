# 🐳 Hướng Dẫn Sử Dụng Docker — Dự Án "AI Là Triệu Phú"

Tài liệu này hướng dẫn chi tiết cách chạy, quản lý và tối ưu ứng dụng **AI Là Triệu Phú** bằng Docker và Docker Compose.

---

## 🚀 1. Lệnh Khởi Chạy Nhanh (Quick Start)

### Chạy ứng dụng + Database PostgreSQL
```bash
docker compose up --build -d
```
- Lệnh trên sẽ build image `millionaire_web`, tải PostgreSQL 16 và khởi tạo dữ liệu tự động.
- Mở trình duyệt truy cập: **http://localhost:5001**

### Chạy kèm Ngrok Tunnel (để nhận Webhook SePay)
```bash
docker compose --profile tunnel up --build -d
```
- Mở Dashboard Ngrok để lấy URL công khai: **http://localhost:4040**

---

## 📋 2. Các Lệnh Quản Lý Container

| Thao tác | Lệnh Shell |
| :--- | :--- |
| **Xem danh sách container đang chạy** | `docker compose ps` |
| **Xem Realtime Logs (Nhật ký app & db)** | `docker compose logs -f` |
| **Xem logs chỉ của Flask App** | `docker compose logs -f web` |
| **Dừng hệ thống (Giữ lại dữ liệu DB)** | `docker compose down` |
| **Dừng & Xóa sạch cả Volume Dữ Liệu** | `docker compose down -v` |
| **Rebuild lại ứng dụng sau khi sửa code** | `docker compose up --build -d web` |

---

## 🛠️ 3. Kiểm Tra Trạng Thái & Debug Database

Muốn truy cập trực tiếp vào Postgres container để truy vấn SQL:
```bash
docker exec -it millionaire_db psql -U postgres -d millionaire
```

Trong psql terminal:
```sql
\dt                  -- Liệt kê các bảng (users, rankings, transactions...)
SELECT * FROM users; -- Kiểm tra dữ liệu người dùng
\q                   -- Thoát
```

---

## ⚡ 4. Tính Năng Tối Ưu Đã Được Cấu Hình
1. **Multi-stage Build**: Giúp Docker image siêu nhẹ (< 200MB) và khởi động cực nhanh.
2. **Auto DB Schema Migration**: Script `docker-entrypoint.sh` tự động chờ Postgres kết nối thành công và tạo bảng (`database.py`, `update_db.py`).
3. **Chế độ WSGI Production**: Dùng Gunicorn với 3 workers + 2 threads xử lý đa nhiệm hiệu quả, chống treo server.
4. **Data Persistence**: Thư mục dữ liệu DB được lưu ở `postgres_data` volume độc lập.
