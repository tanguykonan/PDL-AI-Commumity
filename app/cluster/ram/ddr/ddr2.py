"""Multi-layer advanced memory architecture (DDR2): User profiles, server feeds, and context builder."""

import os
import json
import datetime
from typing import Optional
from collections import deque
from app.helps.utils import logger
from settings.config import params


class UserProfile:
    """Persistent structure tracking user traits, topics, facts, and conversation history."""

    __slots__ = (
        "user_id",
        "username",
        "first_seen",
        "last_seen",
        "message_count",
        "preferred_language",
        "topics",
        "key_facts",
        "tone_preference",
        "notes",
    )

    def __init__(self, user_id: str, username: str = ""):
        self.user_id = user_id
        self.username = username
        self.first_seen = datetime.datetime.now().isoformat()
        self.last_seen = self.first_seen
        self.message_count = 0
        self.preferred_language = "fr"
        self.topics = []
        self.key_facts = []
        self.tone_preference = "neutre"
        self.notes = ""

    def touch(self, username: str = ""):
        """Update last seen timestamp and increment message counter."""
        self.last_seen = datetime.datetime.now().isoformat()
        self.message_count += 1
        if username:
            self.username = username

    def to_dict(self) -> dict:
        """Convert profile to serializable dictionary."""
        return {s: getattr(self, s) for s in self.__slots__}

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        """Reconstruct UserProfile instance from dictionary."""
        p = cls.__new__(cls)
        for s in cls.__slots__:
            setattr(p, s, data.get(s, [] if s in ("topics", "key_facts") else ""))
        return p

    def to_context_string(self) -> str:
        """Generate human-readable summary injected into LLM system prompt."""
        parts = [f"User: {self.username} (ID {self.user_id})"]
        if self.key_facts:
            parts.append("Known facts: " + " | ".join(self.key_facts[:5]))
        if self.topics:
            parts.append("Recurring topics: " + ", ".join(self.topics[:5]))
        if self.tone_preference != "neutre":
            parts.append(f"Preferred tone: {self.tone_preference}")
        if self.notes:
            parts.append(f"Notes: {self.notes}")
        parts.append(f"Messages exchanged: {self.message_count}")
        return "\n".join(parts)


class UserMemory:
    """User conversation history, profile attributes, and session summary."""

    def __init__(self, user_id: str, username: str = ""):
        self.user_id = user_id
        self.history = deque(maxlen=params.META_USER_LIMIT)
        self.profile = UserProfile(user_id, username)
        self.summary = ""
        self.last_active = datetime.datetime.now()
        self.dirty = False

    def add(self, content: str, role: str = "user", username: str = "") -> int:
        """Append message to user history. Returns updated history length."""
        if self.history and self.history[-1]["content"] == content:
            return len(self.history)

        self.history.append({"role": role, "content": content})
        self.last_active = datetime.datetime.now()
        self.profile.touch(username)
        self.dirty = True
        return len(self.history)

    def get_recent(self, n: int = params.META_CONTEXT_MESSAGES) -> list:
        """Return the N most recent messages."""
        msgs = list(self.history)
        return msgs[-n:] if n > 0 else msgs

    def is_inactive(self, max_hours: float = params.META_INACTIVE_TIME) -> bool:
        """Check if user has been inactive beyond threshold."""
        delta = (datetime.datetime.now() - self.last_active).total_seconds()
        return delta > max_hours * 3600

    def to_dict(self) -> dict:
        """Serialize UserMemory state."""
        return {
            "user_id": self.user_id,
            "history": list(self.history),
            "profile": self.profile.to_dict(),
            "summary": self.summary,
            "last_active": self.last_active.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserMemory":
        """Deserialize UserMemory state."""
        obj = cls.__new__(cls)
        obj.user_id = data["user_id"]
        obj.history = deque(data.get("history", []), maxlen=params.META_USER_LIMIT)
        obj.profile = UserProfile.from_dict(data.get("profile", {"user_id": data["user_id"]}))
        obj.summary = data.get("summary", "")
        obj.last_active = datetime.datetime.fromisoformat(
            data.get("last_active", datetime.datetime.now().isoformat())
        )
        obj.dirty = False
        return obj


class ServerMemory:
    """Global guild message feed tracking activity across text channels."""

    def __init__(self, server_id: str):
        self.server_id = server_id
        self.feed = deque(maxlen=params.META_SERVER_LIMIT)
        self.channels = {}
        self.dirty = False
        self.last_active = datetime.datetime.now()

    def add(
        self,
        author_id: str,
        author_name: str,
        channel_id: str,
        channel_name: str,
        content: str,
    ):
        """Append message to global and channel-specific feed."""
        entry = {
            "author_id": str(author_id),
            "author_name": author_name,
            "channel_id": str(channel_id),
            "channel_name": channel_name,
            "content": content,
            "ts": datetime.datetime.now().isoformat(),
        }
        self.feed.append(entry)

        cid = str(channel_id)
        if cid not in self.channels:
            self.channels[cid] = deque(maxlen=params.META_SERVER_LIMIT // 4)
        self.channels[cid].append(entry)
        self.dirty = True
        self.last_active = datetime.datetime.now()

    def is_inactive(self, max_hours: float = params.META_INACTIVE_TIME) -> bool:
        """Check if server has been inactive beyond threshold."""
        delta = (datetime.datetime.now() - self.last_active).total_seconds()
        return delta > max_hours * 3600

    def get_recent_feed(self, n: int = params.META_SERVER_INJECT) -> list:
        """Return the N most recent global server messages."""
        return list(self.feed)[-n:]

    def get_channel_feed(self, channel_id: str, n: int = params.META_SERVER_INJECT) -> list:
        """Return the N most recent messages in a specific channel."""
        cid = str(channel_id)
        return list(self.channels.get(cid, []))[-n:]

    def to_dict(self) -> dict:
        """Serialize ServerMemory state."""
        return {
            "server_id": self.server_id,
            "feed": list(self.feed),
            "channels": {k: list(v) for k, v in self.channels.items()},
            "last_active": self.last_active.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ServerMemory":
        """Deserialize ServerMemory state."""
        obj = cls.__new__(cls)
        obj.server_id = data["server_id"]
        obj.feed = deque(data.get("feed", []), maxlen=params.META_SERVER_LIMIT)
        obj.channels = {
            k: deque(v, maxlen=params.META_SERVER_LIMIT // 4)
            for k, v in data.get("channels", {}).items()
        }
        obj.dirty = False
        obj.last_active = datetime.datetime.fromisoformat(
            data.get("last_active", datetime.datetime.now().isoformat())
        )
        return obj


class ContextBuilder:
    """Combines UserMemory, ServerMemory, and summaries into a complete message payload for Groq."""

    @staticmethod
    def build(
        user_mem: UserMemory,
        server_mem: Optional[ServerMemory] = None,
        channel_id: Optional[str] = None,
    ) -> list:
        """Build structured context payload."""
        messages, context_parts = [], []
        context_parts.append(f"━━━ USER PROFILE ━━━\n{user_mem.profile.to_context_string()}")

        if server_mem:
            feed = (
                server_mem.get_channel_feed(channel_id, params.META_SERVER_INJECT)
                if channel_id
                else server_mem.get_recent_feed(params.META_SERVER_INJECT)
            )
            if feed:
                lines = [
                    f"[{e['ts'][11:16]}] #{e['channel_name']} {e['author_name']}: {e['content'][:120]}"
                    for e in feed
                ]
                context_parts.append("━━━ GUILD CONTEXT ━━━\n" + "\n".join(lines))

        if user_mem.summary:
            context_parts.append(f"━━━ SUMMARY ━━━\n{user_mem.summary}")

        if context_parts:
            messages.append({"role": "user", "content": "[INTERNAL CONTEXT]\n" + "\n\n".join(context_parts)})
            messages.append({"role": "assistant", "content": "Context received."})

        messages.extend(user_mem.get_recent(params.META_CONTEXT_MESSAGES))
        return messages


class AdvancedMemory:
    """Main memory orchestrator providing unified cache, persistence, and querying."""

    def __init__(self, memory_path: str = params.META_PATH):
        self.users_path = os.path.join(memory_path, "users")
        self.servers_path = os.path.join(memory_path, "servers/thread")
        self.users: dict[str, UserMemory] = {}
        self.servers: dict[str, ServerMemory] = {}
        self._ops: int = 0
        self._load()

    def manage(
        self,
        user_id: str,
        message_content: str,
        role: str = "user",
        username: str = "",
    ) -> int:
        """Append message to user conversation context."""
        uid = str(user_id)
        umem = self._get_user(uid, username)
        size = umem.add(message_content, role, username)
        self._auto_save()
        return size

    def get_history(self, user_id: str, limit: Optional[int] = None) -> list:
        """Retrieve recent conversation history for user."""
        uid = str(user_id)
        umem = self.users.get(uid)
        if not umem:
            return []
        return umem.get_recent(limit or params.META_CONTEXT_MESSAGES)

    def delete_history(self, user_id: str) -> bool:
        """Delete user history from memory and disk."""
        uid = str(user_id)
        if uid in self.users:
            del self.users[uid]
            path = os.path.join(self.users_path, f"{uid}.json")
            if os.path.exists(path):
                os.remove(path)
            return True
        return False

    def add_server_message(
        self,
        server_id: str,
        author_id: str,
        author_name: str,
        channel_id: str,
        channel_name: str,
        content: str,
    ):
        """Record message in global server feed."""
        sid = str(server_id)
        smem = self._get_server(sid)
        smem.add(str(author_id), author_name, str(channel_id), channel_name, content)
        self._auto_save()

    def get_server_feed(self, server_id: str, n: int = params.META_SERVER_INJECT) -> list:
        """Get recent messages from server feed."""
        smem = self.servers.get(str(server_id))
        return smem.get_recent_feed(n) if smem else []

    def build_context(
        self,
        user_id: str,
        server_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        username: str = "",
    ) -> list:
        """Build assembled prompt messages for Groq API."""
        uid = str(user_id)
        umem = self._get_user(uid, username)
        smem = self.servers.get(str(server_id)) if server_id else None

        return ContextBuilder.build(
            user_mem=umem,
            server_mem=smem,
            channel_id=str(channel_id) if channel_id else None,
        )

    def update_profile(
        self,
        user_id: str,
        key_facts: Optional[list] = None,
        topics: Optional[list] = None,
        tone: Optional[str] = None,
        notes: Optional[str] = None,
        language: Optional[str] = None,
    ):
        """Update user profile traits."""
        uid = str(user_id)
        umem = self._get_user(uid)

        if key_facts is not None:
            existing = set(umem.profile.key_facts)
            for fact in key_facts:
                if fact not in existing:
                    umem.profile.key_facts.append(fact)
            umem.profile.key_facts = umem.profile.key_facts[-20:]

        if topics is not None:
            existing = set(umem.profile.topics)
            for t in topics:
                if t not in existing:
                    umem.profile.topics.append(t)
            umem.profile.topics = umem.profile.topics[-15:]

        if tone is not None:
            umem.profile.tone_preference = tone
        if notes is not None:
            umem.profile.notes = notes
        if language is not None:
            umem.profile.preferred_language = language

        umem.dirty = True
        self._auto_save()

    def set_summary(self, user_id: str, summary: str):
        """Set session summary for user."""
        uid = str(user_id)
        umem = self._get_user(uid)
        umem.summary = summary
        umem.dirty = True
        self._auto_save()

    def should_summarize(self, user_id: str) -> bool:
        """Check if history size exceeds summary threshold."""
        uid = str(user_id)
        umem = self.users.get(uid)
        return bool(umem and len(umem.history) >= params.META_SUMMARY_THRESHOLD)

    def get_summary_prompt(self, user_id: str) -> Optional[list]:
        """Generate prompt for LLM session summarization."""
        uid = str(user_id)
        umem = self.users.get(uid)
        if not umem:
            return None

        history_text = "\n".join(
            f"[{m['role'].upper()}]: {m['content'][:200]}" for m in list(umem.history)
        )
        return [
            {
                "role": "system",
                "content": (
                    "You are a summarization assistant. "
                    "Summarize in 5 key bullet points this Discord conversation. "
                    "Be concise, factual, and retain key user context."
                ),
            },
            {"role": "user", "content": f"Conversation to summarize:\n{history_text}"},
        ]

    def trim_after_summary(self, user_id: str, keep_last: int = 10):
        """Trim history after generating summary."""
        uid = str(user_id)
        umem = self.users.get(uid)
        if umem:
            recent = umem.get_recent(keep_last)
            umem.history = deque(recent, maxlen=params.META_USER_LIMIT)
            umem.dirty = True

    def clear_memory(self, max_inactive_hours: float = params.META_INACTIVE_TIME) -> int:
        """Purge inactive user and server caches."""
        to_remove = [
            uid for uid, umem in self.users.items() if umem.is_inactive(max_inactive_hours)
        ]
        for uid in to_remove:
            del self.users[uid]
            path = os.path.join(self.users_path, f"{uid}.json")
            if os.path.exists(path):
                os.remove(path)

        servers_to_remove = [
            sid for sid, smem in self.servers.items() if smem.is_inactive(max_inactive_hours)
        ]
        for sid in servers_to_remove:
            del self.servers[sid]
            path = os.path.join(self.servers_path, f"{sid}.json")
            if os.path.exists(path):
                os.remove(path)

        return len(to_remove) + len(servers_to_remove)

    def stats(self) -> dict:
        """Return memory statistics."""
        return {
            "users_in_memory": len(self.users),
            "servers_tracked": len(self.servers),
            "total_messages": sum(len(u.history) for u in self.users.values()),
            "total_server_msgs": sum(len(s.feed) for s in self.servers.values()),
        }

    def save_to_file(self) -> bool:
        """Force save state to disk."""
        return self._save()

    def _get_user(self, uid: str, username: str = "") -> UserMemory:
        if uid not in self.users:
            self.users[uid] = UserMemory(uid, username)
        elif username:
            self.users[uid].profile.username = username
        return self.users[uid]

    def _get_server(self, sid: str) -> ServerMemory:
        if sid not in self.servers:
            self.servers[sid] = ServerMemory(sid)
        return self.servers[sid]

    def _auto_save(self):
        self._ops += 1
        if self._ops >= params.META_SAVE_EVERY:
            self._save()
            self._ops = 0

    def _save(self) -> bool:
        try:
            os.makedirs(self.users_path, exist_ok=True)
            os.makedirs(self.servers_path, exist_ok=True)

            for uid, umem in self.users.items():
                if umem.dirty:
                    path = os.path.join(self.users_path, f"{uid}.json")
                    tmp = path + ".tmp"
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump(umem.to_dict(), f, ensure_ascii=False, indent=2)
                    os.replace(tmp, path)
                    umem.dirty = False

            for sid, smem in self.servers.items():
                if smem.dirty:
                    path = os.path.join(self.servers_path, f"{sid}.json")
                    tmp = path + ".tmp"
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump(smem.to_dict(), f, ensure_ascii=False, indent=2)
                    os.replace(tmp, path)
                    smem.dirty = False

            return True
        except Exception as e:
            logger.error(f"[MEMORY v2] Error saving memory: {e}", exc_info=True)
            return False

    def _load(self) -> bool:
        try:
            os.makedirs(self.users_path, exist_ok=True)
            os.makedirs(self.servers_path, exist_ok=True)

            for filename in os.listdir(self.users_path):
                if filename.endswith(".json"):
                    uid = filename[:-5]
                    path = os.path.join(self.users_path, filename)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            self.users[uid] = UserMemory.from_dict(json.load(f))
                    except (json.JSONDecodeError, KeyError) as err:
                        logger.error(f"[ERROR DDR2] Corrupt user file ignored ({filename}): {err}", exc_info=True)
                        continue

            for filename in os.listdir(self.servers_path):
                if filename.endswith(".json"):
                    sid = filename[:-5]
                    path = os.path.join(self.servers_path, filename)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            self.servers[sid] = ServerMemory.from_dict(json.load(f))
                    except (json.JSONDecodeError, KeyError) as err:
                        logger.error(f"[ERROR DDR2] Corrupt server file ignored ({filename}): {err}", exc_info=True)
                        continue

            return True
        except Exception as e:
            logger.error(f"[ERROR DDR2] Error loading memory: {e}", exc_info=True)
            return False

    def __del__(self):
        dirty = any(u.dirty for u in self.users.values()) or any(s.dirty for s in self.servers.values())
        if dirty:
            self._save()


RandomAccessMemory = AdvancedMemory
