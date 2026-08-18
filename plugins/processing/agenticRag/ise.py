"""Internal Search Engine (ISE) for server-specific logs and activity context."""

import os
import json
from typing import Optional, Dict, List
from app.helps.utils import logger
from settings.config import params


class InternalSearchEngine:
    """Manages local server-level JSONL log files for contextual search."""

    def __init__(self, directory: str = params.RAG_PATH):
        self.directory = directory
        self.max_lines = params.RAG_FILE_MAX_LINES
        self.cache: Dict[str, tuple] = {}

        if not os.path.exists(self.directory):
            os.makedirs(self.directory, exist_ok=True)

    def _create_rag_file(self, server: str) -> str:
        """Ensure the server-specific log file exists and return its path."""
        path = os.path.join(self.directory, f"rag_{server}.jsonl")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8"):
                pass
        return path

    def _limiter_rag_file(self, path: str) -> bool:
        """Limit the file line count to prevent excessive storage growth."""
        try:
            with open(path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            if len(lines) > self.max_lines:
                with open(path, "w", encoding="utf-8") as file:
                    file.writelines(lines[-self.max_lines:])
            return True
        except Exception as error:
            logger.error(f"[ERROR RAG] Failed to truncate log file: {error}", exc_info=True)
            return False

    def _load_rag_file(self, server: str) -> list:
        """Load and parse JSONL records for a specific server."""
        try:
            path = self._create_rag_file(server)
            if not os.path.exists(path):
                return []

            mtime = os.path.getmtime(path)
            cache_key = path
            if cache_key in self.cache:
                cached_mtime, cached_data = self.cache[cache_key]
                if cached_mtime == mtime:
                    return cached_data

            data = []
            with open(path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if line:
                        try:
                            data.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

            self.cache[cache_key] = (mtime, data)
            return data
        except Exception as error:
            logger.error(f"[ERROR RAG] Failed to load server log file: {error}", exc_info=True)
            return []

    async def store_rag_data(self, server: str, data: dict):
        """Append a new record to the server's local JSONL log."""
        try:
            path = self._create_rag_file(server)
            with open(path, "a", encoding="utf-8") as file:
                file.write(json.dumps(data, ensure_ascii=False) + "\n")

            if os.path.getsize(path) > (self.max_lines * 150):
                self._limiter_rag_file(path)
        except Exception as error:
            logger.error(f"[ERROR RAG] Failed to store server log data: {error}", exc_info=True)

    async def call_rag_analyzer(self, message: str, server: str) -> Optional[str]:
        """Retrieve and format server context logs directly for the main chat engine."""
        try:
            rag_data = self._load_rag_file(server)
            if not rag_data:
                return "RAS"

            # Format the most recent server entries for the LLM to inspect
            formatted_entries = []
            for entry in rag_data[-self.max_lines:]:
                if isinstance(entry, dict):
                    author = entry.get("author", entry.get("user", "Utilisateur"))
                    content = entry.get("content", entry.get("message", ""))
                    date = entry.get("date", entry.get("timestamp", ""))
                    date_prefix = f"[{date}] " if date else ""
                    formatted_entries.append(f"{date_prefix}{author}: {content}")
                else:
                    formatted_entries.append(str(entry))

            if not formatted_entries:
                return "RAS"

            return "\n".join(formatted_entries)
        except Exception as error:
            logger.error(f"[ERROR RAG] Failed to retrieve server logs: {error}", exc_info=True)
            return "RAS"