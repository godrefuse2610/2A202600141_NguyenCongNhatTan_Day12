FROM python:3.11-slim

WORKDIR /app

# Cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Môi trường
ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

# Lệnh chạy app
CMD ["python", "app.py"]
