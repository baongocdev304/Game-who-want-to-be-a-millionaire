# ============================================================
# STAGE 1: Builder (Cài đặt dependencies và chuẩn bị virtualenv)
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Cài đặt công cụ build cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Tạo Virtual Environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy và cài đặt python modules
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================
# STAGE 2: Runner (Image runtime siêu gọn & bảo mật)
# ============================================================
FROM python:3.11-slim AS runner

# Cài đặt thư viện phụ trợ runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Sao chép virtual environment từ builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Tạo user không phải root để tăng tính bảo mật
RUN addgroup --system appuser && adduser --system --group appuser

WORKDIR /app

# Copy mã nguồn dự án vào container
COPY --chown=appuser:appuser . /app

# Cấp quyền thực thi cho entrypoint script
RUN chmod +x /app/docker-entrypoint.sh

# Chuyển sang user appuser
USER appuser

# Expose port 5001
EXPOSE 5001

# Entrypoint script xử lý wait-for-DB & migration
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Lệnh khởi chạy ứng dụng mặc định bằng Gunicorn WSGI Server
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "3", "--threads", "2", "--timeout", "120", "app:app"]
