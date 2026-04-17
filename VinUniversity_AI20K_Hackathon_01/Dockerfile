# ============================================================
# Production Dockerfile — Multi-stage with Virtualenv
# ============================================================

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Cài đặt công cụ build
RUN apt-get update && apt-get install -y gcc g++ libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Tạo virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Runtime
FROM python:3.11-slim AS runtime

# Tạo user không phải root
RUN groupadd -r vinlex && useradd -r -g vinlex -d /app vinlex

WORKDIR /app

# Copy virtual environment từ builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy mã nguồn ứng dụng
COPY . .

# Cấp quyền cho user vinlex
RUN chown -R vinlex:vinlex /app && chmod -R 755 /app

USER vinlex

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Railway gán cổng động qua biến $PORT
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c \
    "import urllib.request; import os; port = os.getenv('PORT', '5000'); urllib.request.urlopen(f'http://localhost:{port}/health')" \
    || exit 1

# Khởi chạy gunicorn từ venv
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 app:app"]

