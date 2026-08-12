#!/bin/sh
set -e

echo "🚀 Starting AI Là Triệu Phú Docker Entrypoint..."

# Kiểm tra kết nối tới Database
if [ -n "$DB_HOST" ]; then
    echo "⏳ Đang chờ PostgreSQL tại $DB_HOST:$DB_PORT sẵn sàng..."
    python3 -c "
import socket, time, os
host = os.environ.get('DB_HOST', 'db')
port = int(os.environ.get('DB_PORT', 5432))
for i in range(30):
    try:
        s = socket.create_connection((host, port), timeout=2)
        s.close()
        print('✅ Database host đang hoạt động!')
        break
    except Exception:
        time.sleep(1)
else:
    print('❌ Không thể kết nối tới Database sau 30s!')
    exit(1)
"
fi

# Tự động khởi tạo schema database và bảng phụ
echo "📦 Kiểm tra & cập nhật Database Schema..."
python3 database.py || echo "⚠️ Cảnh báo: Tự động chạy database.py gặp lỗi hoặc bảng đã tồn tại."
python3 update_db.py || echo "⚠️ Cảnh báo: Tự động chạy update_db.py gặp lỗi hoặc bảng đã tồn tại."

echo "✅ Khởi tạo Database hoàn tất. Đang khởi động ứng dụng..."
exec "$@"
