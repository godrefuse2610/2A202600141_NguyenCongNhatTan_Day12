# ============================================================
# Production Dockerfile — Multi-stage
# ============================================================

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y gcc g++ libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

# Non-root user
RUN groupadd -r vinlex && useradd -r -g vinlex -d /app vinlex

WORKDIR /app

# Copy packages từ builder
COPY --from=builder /root/.local /home/vinlex/.local

# Copy application
COPY . .

RUN chown -R vinlex:vinlex /app

USER vinlex

ENV PATH=/home/vinlex/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Railway will override this with its own PORT
EXPOSE 5000

# Health check (sử dụng cổng 5000 làm mặc định hoặc fallback)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c \
    "import urllib.request; import os; port = os.getenv('PORT', '5000'); urllib.request.urlopen(f'http://localhost:{port}/health')" \
    || exit 1

# Sử dụng biến môi trường PORT cho gunicorn
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 app:app"]

