import json
import os
import uuid
import redis
from datetime import datetime, timezone
from config import MEMORY_WINDOW

class ConversationMemory:
    """Quản lý lịch sử hội thoại dùng Redis để hỗ trợ stateless scaling."""

    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.r = redis.from_url(redis_url, decode_responses=True)
            self.r.ping()
            self.use_redis = True
        except Exception:
            self.use_redis = False

    def _get_conv_key(self, session_id, conv_id):
        return f"vinlex:conv:{session_id}:{conv_id}"

    def _get_list_key(self, session_id):
        return f"vinlex:conv_list:{session_id}"

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def get_conversations(self, session_id):
        if not self.use_redis: return []
        list_key = self._get_list_key(session_id)
        conv_ids = self.r.smembers(list_key)
        convs = []
        for cid in conv_ids:
            data_json = self.r.get(self._get_conv_key(session_id, cid))
            if data_json:
                data = json.loads(data_json)
                convs.append({
                    "id": data["id"],
                    "title": data.get("title", "Cuộc trò chuyện mới"),
                    "updated_at": data.get("updated_at", ""),
                    "message_count": len(data.get("messages", [])),
                })
        convs.sort(key=lambda x: x["updated_at"], reverse=True)
        return convs

    def create_conversation(self, session_id):
        conv_id = str(uuid.uuid4())
        now = self._now()
        data = {
            "id": conv_id,
            "session_id": session_id,
            "title": "Cuộc trò chuyện mới",
            "created_at": now,
            "updated_at": now,
            "messages": [],
        }
        if self.use_redis:
            self.r.set(self._get_conv_key(session_id, conv_id), json.dumps(data))
            self.r.sadd(self._get_list_key(session_id), conv_id)
            self.r.expire(self._get_conv_key(session_id, conv_id), 7 * 24 * 3600)
        return data

    def get_conversation(self, session_id, conv_id):
        if not self.use_redis: return None
        data_json = self.r.get(self._get_conv_key(session_id, conv_id))
        return json.loads(data_json) if data_json else None

    def add_message(self, session_id, conv_id, role, content, sources=None, query_type=None):
        data = self.get_conversation(session_id, conv_id)
        if not data: return
        msg = {"role": role, "content": content, "timestamp": self._now()}
        if sources: msg["sources"] = sources
        if query_type: msg["query_type"] = query_type
        data["messages"].append(msg)
        data["updated_at"] = self._now()
        if data["title"] == "Cuộc trò chuyện mới" and role == "user":
            data["title"] = content[:60]
        if self.use_redis:
            self.r.set(self._get_conv_key(session_id, conv_id), json.dumps(data))

    def get_recent_messages(self, session_id, conv_id, n=MEMORY_WINDOW):
        data = self.get_conversation(session_id, conv_id)
        if not data: return []
        messages = data.get("messages", [])
        return messages[-n:]

    def delete_conversation(self, session_id, conv_id):
        """Xóa cuộc trò chuyện khỏi Redis."""
        if not self.use_redis: return
        self.r.delete(self._get_conv_key(session_id, conv_id))
        self.r.srem(self._get_list_key(session_id), conv_id)
