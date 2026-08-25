"""Legacy short-term conversational memory manager (DDR1)."""

import os
import json
import datetime
from app.helps.utils import logger
from settings.config import params

meta_path = os.path.join(params.META_PATH, "meta.json")


class RandomAccessMemory:
    """In-memory conversation history cache with persistence to disk."""

    def __init__(self, memory_limit=params.META_LIMIT):
        try:
            self.memory_limit = memory_limit
            self.memory = {}
            self.lastMessageTime = {}
            self.modified = False
            self.load_from_file()
        except Exception as error:
            logger.error(f"[MEMORY ERROR] Error initializing DDR1 memory: {error}", exc_info=True)

    def clear_memory(self, max_inactive_time=params.META_INACTIVE_TIME * 3600):
        """Purge conversations for inactive users exceeding threshold."""
        try:
            now = datetime.datetime.now()
            to_remove = []

            for user_id, last_time in self.lastMessageTime.items():
                if (now - last_time).total_seconds() > max_inactive_time:
                    to_remove.append(user_id)

            for user_id in to_remove:
                self.memory.pop(user_id, None)
                self.lastMessageTime.pop(user_id, None)
                self.modified = True

            if self.modified:
                self.save_to_file()

            return len(to_remove)
        except Exception as error:
            logger.error(f"[MEMORY ERROR] Failed to clear inactive memory: {error}", exc_info=True)
            return 0

    def manage(self, user_id, message_content, role="user"):
        """Append message to user conversation context."""
        try:
            user_id = str(user_id)
            if user_id not in self.memory:
                self.memory[user_id] = []

            message = {"role": role, "content": message_content}

            if not self.memory[user_id] or self.memory[user_id][-1]["content"] != message_content:
                self.memory[user_id].append(message)
                self.modified = True

            self.lastMessageTime[user_id] = datetime.datetime.now()

            if 0 < self.memory_limit < len(self.memory[user_id]):
                self.memory[user_id] = self.memory[user_id][-self.memory_limit :]
                self.modified = True

            if self.modified and len(self.memory[user_id]) % 5 == 0:
                self.save_to_file()

            return len(self.memory[user_id])
        except Exception as error:
            logger.error(f"[MEMORY ERROR] Failed to append message to user memory: {error}", exc_info=True)
            return 0

    def get_history(self, user_id, limit=None):
        """Retrieve recent conversation history for a given user."""
        try:
            user_id = str(user_id)
            history = self.memory.get(user_id, [])
            if limit and limit > 0:
                history = history[-limit:]
            return history
        except Exception as error:
            logger.error(f"[MEMORY ERROR] Failed to retrieve user history: {error}", exc_info=True)
            return []

    def delete_history(self, user_id):
        """Delete conversation history for a user."""
        try:
            user_id = str(user_id)
            if user_id in self.memory:
                del self.memory[user_id]
                del self.lastMessageTime[user_id]
                self.modified = True
                self.save_to_file()
                return True
            return False
        except Exception as error:
            logger.error(f"[MEMORY ERROR] Failed to delete user history: {error}", exc_info=True)
            return False

    def save_to_file(self):
        """Persist in-memory state to disk."""
        try:
            os.makedirs(os.path.dirname(meta_path), exist_ok=True)
            data = {
                "conversations": self.memory,
                "lastMessageTime": {k: v.isoformat() for k, v in self.lastMessageTime.items()},
            }

            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            self.modified = False
            return True
        except Exception as error:
            logger.error(f"[MEMORY ERROR] Failed to save memory state: {error}", exc_info=True)
            return False

    def load_from_file(self):
        """Load persisted state from disk into memory."""
        try:
            if not os.path.exists(meta_path):
                os.makedirs(os.path.dirname(meta_path), exist_ok=True)
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump({"conversations": {}, "lastMessageTime": {}}, f)
                return True

            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.memory = data.get("conversations", {})
                self.lastMessageTime = {
                    k: datetime.datetime.fromisoformat(v)
                    for k, v in data.get("lastMessageTime", {}).items()
                }
            return True
        except json.decoder.JSONDecodeError as e:
            logger.error(f"[MEMORY ERROR] JSON decode error loading memory: {e}", exc_info=True)
            self.memory = {}
            self.lastMessageTime = {}
            self.save_to_file()
            return False
        except Exception as error:
            logger.error(f"[ERROR MEMORY] Failed to load memory state: {error}", exc_info=True)
            return False

    def __del__(self):
        if self.modified:
            self.save_to_file()