# Day 12 Lab - Mission Answers

> **Student Name:** Nguyễn Công Nhật Tân  
> **Student ID:** 2A202600141  
> **Date:** 17/4/2026

---

##  Submission Requirements

Submit a **GitHub repository** containing:

### 1. Mission Answers (40 points)

Create a file `MISSION_ANSWERS.md` with your answers to all exercises:

```markdown
# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. **Hardcoded Secrets:** API Key và Database URL được ghi trực tiếp trong mã nguồn (`OPENAI_API_KEY`, `DATABASE_URL`), dễ bị lộ khi push code lên GitHub.
2. **Hardcoded Port & Host:** Host được đặt là `localhost` và port cố định `8000`. Điều này khiến ứng dụng không thể chạy trên các Cloud Platform (vốn cần bind vào host `0.0.0.0` và port do hệ thống cấp qua biến môi trường).
3. **Thiếu Health Check Endpoint:** Không có các endpoint như `/health` hoặc `/ready` để hệ thống giám sát (Monitoring/Orchestrator) biết trạng thái của ứng dụng để tự động restart khi gặp sự cố.
4. **Sử dụng Print thay vì Logging:** Sử dụng hàm `print()` không có cấu trúc, khó quản lý log trong production và đặc biệt nguy hiểm khi log cả thông tin nhạy cảm (API Key) ra console.
5. **Chế độ Debug/Reload bật sẵn:** Biến `DEBUG = True` và `reload=True` được bật. Điều này gây rủi ro bảo mật và tiêu tốn tài nguyên không cần thiết khi chạy thực tế.

### Exercise 1.3: Comparison table
| Feature | Basic (Develop) | Advanced (Production) | Tại sao quan trọng? |
|---------|-------|----------|---------------------|
| Config | Hardcode trong code | Environment Variables (Pydantic Settings) | Bảo mật thông tin nhạy cảm và linh hoạt thay đổi cấu hình giữa các môi trường (Dev/Prod) mà không cần sửa code. |
| Health check | Không có | Có endpoint `/health` và `/ready` | Giúp Platform tự động giám sát, restart container khi lỗi và chỉ gửi traffic khi ứng dụng đã sẵn sàng. |
| Logging | Sử dụng `print()` | Structured JSON Logging | Giúp hệ thống tập trung log dễ dàng phân tích và tránh việc vô tình in các thông tin bí mật ra log. |
| Shutdown | Tắt đột ngột | Graceful Shutdown (SIGTERM handler) | Đảm bảo hoàn thành các request đang dở dang trước khi đóng ứng dụng, tránh gây lỗi cho người dùng. |
| Port/Host | Cố định (localhost:8000) | Linh hoạt (0.0.0.0 và dynamic PORT) | Cho phép ứng dụng nhận kết nối từ bên ngoài (Internet) và chạy được trong môi trường Container/Cloud. |
...

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image là gì?**  
   Base image là `python:3.11`. Đây là bản phân phối Python đầy đủ, dung lượng khoảng 1GB.

2. **Working directory là gì?**  
   Working directory trong container là `/app`. Tất cả các câu lệnh sau đó (COPY, RUN, CMD) sẽ được thực hiện tương đối với thư mục này.

3. **Tại sao COPY requirements.txt trước?**  
   Để tận dụng **Docker layer caching**. Docker sẽ lưu cache cho từng layer. Nếu file `requirements.txt` không thay đổi, Docker sẽ bỏ qua bước `pip install` (vốn tốn nhiều thời gian) và dùng bản cache từ build trước đó, ngay cả khi mã nguồn ứng dụng (`app.py`) có thay đổi.

4. **CMD vs ENTRYPOINT khác nhau thế nào?**  
   - `CMD`: Cung cấp các lệnh/tham số mặc định cho container. Nó có thể bị ghi đè hoàn toàn khi ta chạy `docker run <image> <new_command>`.
   - `ENTRYPOINT`: Thiết lập lệnh chính sẽ chạy khi container khởi động. Nó khó bị ghi đè hơn và các tham số truyền vào từ `docker run` sẽ được cộng dồn (append) vào sau lệnh `ENTRYPOINT`. Trong Dockerfile này, `CMD` được dùng để chạy ứng dụng Python.

### Exercise 2.3: Image size comparison
- Develop: 1.14 GB
- Production: 160.38 MB
- Difference: 85.94%

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://2a202600141nguyencongnhattanday12-production.up.railway.app
- Screenshot: day12/2A202600141_NguyenCongNhatTan_Day12/02-docker/production/Screenshot_app.png

## Part 4: API Security

### Exercise 4.1-4.3: Test results
[Paste your test outputs]
4.1: Không key:
$ curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}

4.1: Có key: 
$ curl -X POST "http://localhost:8000/ask?question=Hello" \
         -H "X-API-Key: demo-key-change-in-production"
{"question":"Hello","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic."}

4.2: lấy token
$ curl http://localhost:8000/auth/token -X POST   -H "Content-Type: application/json"   -d '{"username": "student", "password": "demo123"}'
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIiLCJpYXQiOjE3NzY0Mjk3OTYsImV4cCI6MTc3NjQzMzM5Nn0.cSTmgQHjmCTnnsddb3imGbspiDR55jtjgpFtKvXyaB0","token_type":"bearer","expires_in_minutes":60,"hint":"Include in header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."}
4.2: Có token 
$ curl http://localhost:8000/ask -X POST   -H "Authorization: Bearer $TOKEN"   -H "Content-Type: application/json"   -d '{"question": "Explain JWT"}'
{"question":"Explain JWT","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","usage":{"requests_remaining":9,"budget_remaining_usd":0.0001068}}

4.3
1. Algorithm được dùng: Sliding Window Counter.
       * Thuật toán này sử dụng một deque để lưu trữ dấu thời gian (timestamps)   
         của các yêu cầu. Khi có yêu cầu mới, các dấu thời gian cũ (ngoài khoảng  
         thời gian 60 giây) sẽ bị loại bỏ trước khi đếm và kiểm tra giới hạn.     

   2. Limit (requests/minute):
       * Đối với người dùng thông thường (rate_limiter_user): 10 requests/minute.
       * Đối với người dùng có quyền Admin (rate_limiter_admin): 100
         requests/minute.

   3. Cách bypass limit cho Admin:
       * Trong tệp app.py (điểm bắt đầu của API), hệ thống sẽ kiểm tra vai trò
         (role) của người dùng từ token hoặc thông tin xác thực.
       * Nếu user["role"] == "admin", hệ thống sẽ sử dụng thực thể
         rate_limiter_admin (có giới hạn cao hơn nhiều là 100 req/phút) thay vì
         rate_limiter_user.
       * Ngoài ra, một số hệ thống API Gateway có thể bypass hoàn toàn nếu không
         gọi hàm check() của rate limiter cho user có role admin, nhưng ở đây
         admin vẫn bị giới hạn ở mức 100 để tránh spam hoặc lỗi vòng lặp vô tận.

Test: 
$ # Gọi liên tục 20 lần
for i in {1..20}; do
  curl http://localhost:8000/ask -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"question": "Test '$i'"}'
  echo ""
done
{"question":"Test 1","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","usage":{"requests_remaining":9,"budget_remaining_usd":0.0001254}}
{"question":"Test 2","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.","usage":{"requests_remaining":8,"budget_remaining_usd":0.0001464}}
{"question":"Test 3","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","usage":{"requests_remaining":7,"budget_remaining_usd":0.000165}}
{"question":"Test 4","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.","usage":{"requests_remaining":6,"budget_remaining_usd":0.000186}}
{"question":"Test 5","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","usage":{"requests_remaining":5,"budget_remaining_usd":0.0002022}}
{"question":"Test 6","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","usage":{"requests_remaining":4,"budget_remaining_usd":0.0002184}}
{"question":"Test 7","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","usage":{"requests_remaining":3,"budget_remaining_usd":0.000237}}
{"question":"Test 8","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","usage":{"requests_remaining":2,"budget_remaining_usd":0.0002532}}
{"question":"Test 9","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","usage":{"requests_remaining":1,"budget_remaining_usd":0.0002694}}
{"question":"Test 10","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","usage":{"requests_remaining":0,"budget_remaining_usd":0.0002856}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":57}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":56}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":56}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":56}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":56}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":55}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":55}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":55}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":55}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":54}}

### Exercise 4.4: Cost guard implementation
Để bảo vệ ngân sách khi sử dụng LLM API, tôi đã triển khai class `CostGuard` với các cơ chế sau:

1. **Lưu trữ trạng thái tập trung (Stateless & Shared):** Sử dụng **Redis** để lưu trữ mức tiêu dùng (cost) theo ngày của từng user và của toàn hệ thống. Điều này đảm bảo khi scale nhiều instance, dữ liệu cost luôn được đồng bộ.
2. **Cơ chế kiểm tra (Pre-check):** Trước khi gọi LLM, hệ thống sẽ kiểm tra:
    * **Global Budget:** Nếu tổng chi phí trong ngày của toàn bộ ứng dụng vượt ngưỡng ($10/ngày), hệ thống sẽ tạm dừng phục vụ (HTTP 503).
    * **Per-user Budget:** Nếu user vượt quá hạn mức cá nhân ($1/ngày), hệ thống trả về lỗi HTTP 402 (Payment Required).
3. **Ghi nhận sử dụng (Post-record):** Sau mỗi lần gọi LLM thành công, số token sử dụng được quy đổi ra USD (dựa trên bảng giá của model) và cập nhật vào Redis bằng lệnh `incrbyfloat` (nguyên tử/atomic).
4. **Tự động reset:** Sử dụng tính năng `EXPIRE` của Redis (32 giờ) để tự động xóa dữ liệu cũ, giúp reset hạn mức sang ngày mới mà không cần chạy cronjob dọn dẹp.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
[Your explanations and test results]

5.2: Test graceful shutdown
```
$ python app.py &
PID=$!

# Gửi request
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Long task"}' &

# Ngay lập tức kill
kill -TERM $PID
[1] 784
[2] 801
2026-04-17 20:09:48,430 INFO Starting agent on port 8000
INFO:     Started server process [2148]
INFO:     Waiting for application startup.
2026-04-17 20:09:48,469 INFO Agent starting up...
2026-04-17 20:09:48,469 INFO Loading model and checking dependencies...
[1]-  Terminated              python app.py

$ curl: (7) Failed to connect to localhost port 8000 after 2240 ms: Couldn't connect to server

5.4:
Khi chạy stack với 3 agent instances (`docker compose up --scale agent=3`), tôi quan sát thấy:
1. **Phân tán tải:** Các request được Nginx (Load Balancer) phân phối luân phiên (Round Robin) đến 3 instance khác nhau (được xác định qua ID instance trong log).
2. **Tính sẵn sàng cao:** Nếu một instance bị lỗi hoặc bị tắt, Nginx tự động phát hiện và chuyển hướng traffic sang các instance còn lại mà không làm gián đoạn dịch vụ.
3. **Log tập trung:** Log từ 3 instance được gom lại, giúp dễ dàng theo dõi tải trọng của toàn hệ thống.

Test log:
```bash
agent-1  | {"ts":"...","lvl":"INFO","msg":"Processing request on instance-d0a9a9"}
agent-2  | {"ts":"...","lvl":"INFO","msg":"Processing request on instance-027688"}
agent-3  | {"ts":"...","lvl":"INFO","msg":"Processing request on instance-710668"}
```
✅ Load balancing hoạt động tốt, giúp hệ thống chịu tải cao hơn và tăng tính ổn định.

5.5: 
PS C:\Users\Admin\LAB\day12\2A202600141_NguyenCongNhatTan_Day12\05-scaling-reliability\production> python test_stateless.py
============================================================
Stateless Scaling Demo
============================================================

Session ID: c6fa96e8-4654-4915-97a0-3013920eeed4

Request 1: [instance-d0a9a9]
  Q: What is Docker?
  A: Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!...

Request 2: [instance-027688]
  Q: Why do we need containers?
  A: Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận....      

Request 3: [instance-710668]
  Q: What is Kubernetes?
  A: Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận....      

Request 4: [instance-d0a9a9]
  Q: How does load balancing work?
  A: Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận....      

Request 5: [instance-027688]
  Q: What is Redis used for?
  A: Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé....        

------------------------------------------------------------
Total requests: 5
Instances used: {'instance-710668', 'instance-d0a9a9', 'instance-027688'}
✅ All requests served despite different instances!

--- Conversation History ---
Total messages: 2
  [user]: What is Kubernetes?...
  [assistant]: Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã đư...    

✅ Session history preserved across all instances via Redis!
---

### 2. Full Source Code - Lab 06 Complete (60 points)

Your final production-ready agent with all files:

```
your-repo/
├── app/
│   ├── main.py              # Main application
│   ├── config.py            # Configuration
│   ├── auth.py              # Authentication
│   ├── rate_limiter.py      # Rate limiting
│   └── cost_guard.py        # Cost protection
├── utils/
│   └── mock_llm.py          # Mock LLM (provided)
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Full stack
├── requirements.txt         # Dependencies
├── .env.example             # Environment template
├── .dockerignore            # Docker ignore
├── railway.toml             # Railway config (or render.yaml)
└── README.md                # Setup instructions
```

**Requirements:**
-  All code runs without errors
-  Multi-stage Dockerfile (image < 500 MB)
-  API key authentication
-  Rate limiting (10 req/min)
-  Cost guard ($10/month)
-  Health + readiness checks
-  Graceful shutdown
-  Stateless design (Redis)
-  No hardcoded secrets

---

### 3. Service Domain Link

Create a file `DEPLOYMENT.md` with your deployed service information:

```markdown
# Deployment Information

## Public URL
https://your-agent.railway.app

## Platform
Railway / Render / Cloud Run

## Test Commands

### Health Check
```bash
curl https://your-agent.railway.app/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)
```bash
curl -X POST https://your-agent.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```

## Environment Variables Set
- PORT
- REDIS_URL
- AGENT_API_KEY
- LOG_LEVEL

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
```

##  Pre-Submission Checklist

- [ ] Repository is public (or instructor has access)
- [ ] `MISSION_ANSWERS.md` completed with all exercises
- [ ] `DEPLOYMENT.md` has working public URL
- [ ] All source code in `app/` directory
- [ ] `README.md` has clear setup instructions
- [ ] No `.env` file committed (only `.env.example`)
- [ ] No hardcoded secrets in code
- [ ] Public URL is accessible and working
- [ ] Screenshots included in `screenshots/` folder
- [ ] Repository has clear commit history

---

##  Self-Test

Before submitting, verify your deployment:

```bash
# 1. Health check
curl https://your-app.railway.app/health

# 2. Authentication required
curl https://your-app.railway.app/ask
# Should return 401

# 3. With API key works
curl -H "X-API-Key: YOUR_KEY" https://your-app.railway.app/ask \
  -X POST -d '{"user_id":"test","question":"Hello"}'
# Should return 200

# 4. Rate limiting
for i in {1..15}; do 
  curl -H "X-API-Key: YOUR_KEY" https://your-app.railway.app/ask \
    -X POST -d '{"user_id":"test","question":"test"}'; 
done
# Should eventually return 429
```

---

##  Submission

**Submit your GitHub repository URL:**

```
https://github.com/your-username/day12-agent-deployment
```

**Deadline:** 17/4/2026

---

##  Quick Tips

1.  Test your public URL from a different device
2.  Make sure repository is public or instructor has access
3.  Include screenshots of working deployment
4.  Write clear commit messages
5.  Test all commands in DEPLOYMENT.md work
6.  No secrets in code or commit history

---

##  Need Help?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [CODE_LAB.md](CODE_LAB.md)
- Ask in office hours
- Post in discussion forum

---

**Good luck! **
