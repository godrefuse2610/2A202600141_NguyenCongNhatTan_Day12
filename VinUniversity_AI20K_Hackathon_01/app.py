import os
import uuid
import logging
import json
from pathlib import Path
from flask import (
    Flask, render_template, request, session,
    redirect, url_for, jsonify, flash
)
from flask_session import Session
import redis
from dotenv import load_dotenv

load_dotenv()

from config import SUGGESTED_QUESTIONS, PDFS_DIR, CHROMA_DIR
from backend.auth import check_credentials, login_required
from backend.memory import ConversationMemory
from backend.pdf_manager import PDFManager
from backend.chatbot import VinLexChatbot
from backend.rate_limiter import rate_limiter
from backend.cost_guard import cost_guard

# ─────────────────────────────────────────────
# Pre-flight: Đảm bảo các thư mục tồn tại
# ─────────────────────────────────────────────
for d in [PDFS_DIR, CHROMA_DIR]:
    os.makedirs(d, exist_ok=True)

# Cấu hình Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-vinlex")

# Cấu hình Redis cho Session (Stateless)
# Ưu tiên lấy REDIS_URL từ Railway, nếu không có mới dùng localhost
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
logger.info(f"Connecting to Redis at: {redis_url.split('@')[-1]}") # Log an toàn không lộ pass

try:
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_REDIS'] = redis.from_url(redis_url)
    Session(app)
except Exception as e:
    logger.error(f"Failed to initialize Redis session: {e}")

# Khởi tạo Singletons
memory = ConversationMemory()
pdf_manager = PDFManager()
chatbot = VinLexChatbot()

@app.before_request
def ensure_session_id():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    
    logger.info(json.dumps({
        "event": "request",
        "method": request.method,
        "path": request.path,
        "ip": request.remote_addr
    }))

# ─────────────────────────────────────────────
# Health & Readiness Checks
# ─────────────────────────────────────────────

@app.get("/health")
def health():
    return jsonify({"status": "ok", "app": "VinLex-Hackathon"})

@app.get("/ready")
def ready():
    try:
        app.config['SESSION_REDIS'].ping()
        return jsonify({"status": "ready"})
    except Exception as e:
        return jsonify({"status": "not ready", "error": str(e)}), 503

# ─────────────────────────────────────────────
# Chat API (Bảo mật & Budget)
# ─────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def api_chat():
    sid = session["session_id"]

    # 1. Rate Limiting check
    if not rate_limiter.is_allowed(sid):
        return jsonify({"error": "Rate limit exceeded. Please wait."}), 429

    # 2. Cost Guard check
    if not cost_guard.check_budget(sid):
        return jsonify({"error": "Budget exceeded"}), 402

    try:
        data = request.get_json(force=True)
        conv_id = data.get("conversation_id")
        message = (data.get("message") or "").strip()

        if not message:
            return jsonify({"error": "Empty message"}), 400

        if not conv_id:
            conv = memory.create_conversation(sid)
            conv_id = conv["id"]
        else:
            conv = memory.get_conversation(sid, conv_id)
            if conv is None:
                conv = memory.create_conversation(sid)
                conv_id = conv["id"]

        memory.add_message(sid, conv_id, role="user", content=message)
        recent = memory.get_recent_messages(sid, conv_id, n=10)
        history = [m for m in recent if m["role"] in ("user", "assistant")]
        # Trừ tin nhắn vừa thêm vào
        history = history[:-1] if history else []

        # Xử lý chatbot
        result = chatbot.process(message, history)

        # 3. Ghi nhận chi phí giả lập
        cost_guard.record_usage(sid, 0.001)

        memory.add_message(
            sid, conv_id,
            role="assistant",
            content=result["answer"],
            sources=result.get("sources", []),
            query_type=result.get("query_type", ""),
        )

        return jsonify({
            "conversation_id": conv_id,
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "query_type": result.get("query_type", ""),
            "redirect_to_contact": result.get("redirect_to_contact", False),
            "suggest_counseling": result.get("suggest_counseling", False)
        })
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────
# Conversation History API
# ─────────────────────────────────────────────

@app.get("/api/conversations")
def api_get_conversations():
    sid = session["session_id"]
    convs = memory.get_conversations(sid)
    return jsonify(convs)

@app.post("/api/conversations")
def api_create_conversation():
    sid = session["session_id"]
    conv = memory.create_conversation(sid)
    return jsonify(conv)

@app.get("/api/conversations/<conv_id>/messages")
def api_get_messages(conv_id):
    sid = session["session_id"]
    conv = memory.get_conversation(sid, conv_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404
    return jsonify(conv.get("messages", []))

@app.delete("/api/conversations/<conv_id>")
def api_delete_conversation(conv_id):
    sid = session["session_id"]
    memory.delete_conversation(sid, conv_id)
    return jsonify({"status": "deleted"})

# ─────────────────────────────────────────────
# PDF Management API
# ─────────────────────────────────────────────

@app.get("/api/pdfs")
@login_required
def api_list_pdfs():
    return jsonify(pdf_manager.list_pdfs())

@app.post("/api/pdfs/upload")
@login_required
def api_upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and file.filename.lower().endswith('.pdf'):
        meta = pdf_manager.upload_pdf(file)
        return jsonify(meta)
    return jsonify({"error": "Invalid file type"}), 400

@app.get("/api/pdfs/<pdf_id>/status")
@login_required
def api_pdf_status(pdf_id):
    status = pdf_manager.get_status(pdf_id)
    if status is None:
        return jsonify({"error": "PDF not found"}), 404
    return jsonify({"status": status})

@app.delete("/api/pdfs/<pdf_id>")
@login_required
def api_delete_pdf(pdf_id):
    success = pdf_manager.delete_pdf(pdf_id)
    if not success:
        return jsonify({"error": "PDF not found"}), 404
    return jsonify({"status": "deleted"})

# ─────────────────────────────────────────────
# Authentication & Pages
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", suggested_questions=SUGGESTED_QUESTIONS, active_tab="chat")

@app.route("/contact")
def contact():
    return render_template("contact.html", active_tab="contact")

@app.route("/management")
@login_required
def management():
    pdfs = pdf_manager.list_pdfs()
    return render_template("management.html", active_tab="management", pdfs=pdfs)

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"): return redirect(url_for("index"))
    if request.method == "POST":
        if check_credentials(request.form.get("username"), request.form.get("password")):
            session["user"] = request.form.get("username")
            return redirect(url_for("index"))
        flash("Sai tên đăng nhập hoặc mật khẩu", "error")
    return render_template("login.html", active_tab="login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
