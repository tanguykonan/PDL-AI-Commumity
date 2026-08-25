"""Local JSON storage manager for servers, users, permissions, and bot statistics."""

import os
import json
import threading
from typing import List, Dict, Any, Optional, Union
from colorama import Fore, Style
from settings.config import params


class Database:
    """Thread-safe JSON database manager with atomic writes."""

    def __init__(self, data_path: str = params.DATABASE_PATH):
        self.data = data_path
        self._lock = threading.RLock()
        self._modified = False
        self.loading = self._get_default_structure()
        if not self.load_data():
            print(Fore.YELLOW + "[WARNING DATABASE] Using default initial structure." + Style.RESET_ALL)

    @staticmethod
    def _get_default_structure() -> Dict[str, Any]:
        """Return fresh database schema."""
        return {
            "bot": {
                "admins": [],
                "activities": [],
                "stats": {
                    "userNumber": 0,
                    "serverNumber": 0,
                    "queryNumber": 0,
                    "usersInMemory": 0,
                    "serversTracked": 0,
                    "totalMessages": 0,
                    "totalServerMessages": 0,
                },
            },
            "users": {},
            "servers": {},
        }

    @staticmethod
    def _get_default_user() -> Dict[str, Any]:
        """Return default user profile schema."""
        return {"isBanned": False}

    @staticmethod
    def _get_default_server() -> Dict[str, Any]:
        """Return default guild settings schema."""
        return {
            "isBanned": False,
            "isPremium": False,
            "config": {
                "language": "fr",
                "mode": "default",
                "alertChannel": None,
                "autoSanction": "Aucune sanction",
            },
            "authorizedChannels": [],
        }

    def load_data(self) -> bool:
        """Load data from JSON file into memory."""
        try:
            if not os.path.exists(self.data) or os.path.getsize(self.data) == 0:
                return self._initialize_database()

            with self._lock:
                with open(self.data, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)

                default_structure = self._get_default_structure()
                self.loading = self._merge_structures(default_structure, loaded_data)

            return True

        except json.JSONDecodeError as error:
            print(Fore.RED + f"[ERROR DATABASE] Corrupt db.json file, re-initializing: {error}" + Style.RESET_ALL)
            return self._initialize_database()

        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Failed to load db.json: {error}" + Style.RESET_ALL)
            return False

    @staticmethod
    def _merge_structures(default: Dict, loaded: Dict) -> Dict:
        """Merge default schema keys with loaded user data."""
        result = default.copy()
        for key, value in loaded.items():
            if key in result:
                if isinstance(value, dict) and isinstance(result[key], dict):
                    result[key] = {**result[key], **value}
                else:
                    result[key] = value
            else:
                result[key] = value
        return result

    def _initialize_database(self) -> bool:
        """Initialize empty database with default schema."""
        try:
            with self._lock:
                self.loading = self._get_default_structure()
                self._modified = True
            self.save_data()
            return True
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error initializing database: {error}" + Style.RESET_ALL)
            return False

    def save_data(self) -> bool:
        """Atomically persist data to disk via a temporary file."""
        tmp_path = f"{self.data}.tmp"
        try:
            os.makedirs(os.path.dirname(self.data), exist_ok=True)
            with self._lock:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(self.loading, f, indent=4, ensure_ascii=False)

                if os.name == "nt":
                    if os.path.exists(self.data):
                        os.remove(self.data)
                    os.rename(tmp_path, self.data)
                else:
                    os.replace(tmp_path, self.data)

                self._modified = False

            return True

        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error saving database: {error}" + Style.RESET_ALL)
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            return False

    def add_admin(self, user_id: Union[int, str]) -> bool:
        """Add user ID to global bot admin list."""
        try:
            with self._lock:
                uid = int(user_id)
                if uid in self.loading["bot"]["admins"]:
                    return False
                self.loading["bot"]["admins"].append(uid)
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in add_admin: {error}" + Style.RESET_ALL)
            return False

    def remove_admin(self, user_id: Union[int, str]) -> bool:
        """Remove user ID from bot admin list."""
        try:
            with self._lock:
                uid = int(user_id)
                if uid not in self.loading["bot"]["admins"]:
                    return False
                self.loading["bot"]["admins"].remove(uid)
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in remove_admin: {error}" + Style.RESET_ALL)
            return False

    def is_admin(self, user_id: Union[int, str]) -> bool:
        """Check if user ID is a global bot administrator."""
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return False
        with self._lock:
            return uid in [int(a) for a in self.loading["bot"]["admins"]]

    def add_activity(self, activity: str) -> bool:
        """Add custom activity string."""
        try:
            with self._lock:
                if activity in self.loading["bot"]["activities"]:
                    return False
                self.loading["bot"]["activities"].append(activity)
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in add_activity: {error}" + Style.RESET_ALL)
            return False

    def remove_activity(self, activity: str) -> bool:
        """Remove custom activity string."""
        try:
            with self._lock:
                if activity not in self.loading["bot"]["activities"]:
                    return False
                self.loading["bot"]["activities"].remove(activity)
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in remove_activity: {error}" + Style.RESET_ALL)
            return False

    def get_activities(self) -> List[str]:
        """Return list of configured activity strings."""
        with self._lock:
            return self.loading["bot"]["activities"].copy()

    def update_stat(self, stat_key: str, value: int) -> bool:
        """Update a specific statistics counter."""
        try:
            with self._lock:
                if stat_key not in self.loading["bot"]["stats"]:
                    return False
                self.loading["bot"]["stats"][stat_key] = value
                self._modified = True
            self.save_data()
            return True
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in update_stat: {error}" + Style.RESET_ALL)
            return False

    def increment_stat(self, stat_key: str, increment: int = 1) -> bool:
        """Increment a specific statistics counter."""
        try:
            with self._lock:
                if stat_key not in self.loading["bot"]["stats"]:
                    return False
                current = self.loading["bot"]["stats"][stat_key]
            return self.update_stat(stat_key, current + increment)
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in increment_stat: {error}" + Style.RESET_ALL)
            return False

    def get_stats(self) -> Dict[str, int]:
        """Return current statistics dictionary."""
        with self._lock:
            return self.loading["bot"]["stats"].copy()

    def _ensure_user(self, user_id: Union[int, str]) -> None:
        """Ensure user profile entry exists in memory."""
        if user_id not in self.loading["users"]:
            self.loading["users"][user_id] = self._get_default_user()

    def ban_user(self, user_id: Union[int, str]) -> bool:
        """Blacklist user from bot interaction."""
        try:
            user_id = str(user_id)
            with self._lock:
                self._ensure_user(user_id)
                self.loading["users"][user_id]["isBanned"] = True
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in ban_user: {error}" + Style.RESET_ALL)
            return False

    def unban_user(self, user_id: Union[int, str]) -> bool:
        """Remove user from blacklist."""
        try:
            user_id = str(user_id)
            with self._lock:
                self._ensure_user(user_id)
                self.loading["users"][user_id]["isBanned"] = False
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in unban_user: {error}" + Style.RESET_ALL)
            return False

    def is_user_banned(self, user_id: Union[int, str]) -> bool:
        """Check if user is blacklisted."""
        user_id = str(user_id)
        with self._lock:
            return self.loading["users"].get(user_id, {}).get("isBanned", False)

    def get_user(self, user_id: Union[int, str]) -> Optional[Dict]:
        """Get user profile dictionary."""
        user_id = str(user_id)
        with self._lock:
            return self.loading["users"].get(user_id, None)

    def _ensure_server(self, server_id: Union[int, str]) -> None:
        """Ensure server settings entry exists in memory."""
        if server_id not in self.loading["servers"]:
            self.loading["servers"][server_id] = self._get_default_server()

    def ban_server(self, server_id: Union[int, str]) -> bool:
        """Blacklist server from bot usage."""
        try:
            server_id = str(server_id)
            with self._lock:
                self._ensure_server(server_id)
                self.loading["servers"][server_id]["isBanned"] = True
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in ban_server: {error}" + Style.RESET_ALL)
            return False

    def unban_server(self, server_id: Union[int, str]) -> bool:
        """Remove server from blacklist."""
        try:
            server_id = str(server_id)
            with self._lock:
                self._ensure_server(server_id)
                self.loading["servers"][server_id]["isBanned"] = False
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in unban_server: {error}" + Style.RESET_ALL)
            return False

    def is_server_banned(self, server_id: Union[int, str]) -> bool:
        """Check if server is blacklisted."""
        server_id = str(server_id)
        with self._lock:
            return self.loading["servers"].get(server_id, {}).get("isBanned", False)

    def set_premium(self, server_id: Union[int, str], state: bool = True) -> bool:
        """Set server premium status."""
        try:
            server_id = str(server_id)
            with self._lock:
                self._ensure_server(server_id)
                self.loading["servers"][server_id]["isPremium"] = state
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in set_premium: {error}" + Style.RESET_ALL)
            return False

    def is_server_premium(self, server_id: Union[int, str]) -> bool:
        """Check if server has premium enabled."""
        server_id = str(server_id)
        with self._lock:
            return self.loading["servers"].get(server_id, {}).get("isPremium", False)

    def set_server_config(self, server_id: Union[int, str], key: str, value: Any) -> bool:
        """Update specific guild configuration key."""
        try:
            server_id = str(server_id)
            with self._lock:
                self._ensure_server(server_id)
                self.loading["servers"][server_id]["config"][key] = value
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in set_server_config: {error}" + Style.RESET_ALL)
            return False

    def get_server_config(self, server_id: Union[int, str]) -> Optional[Dict]:
        """Get guild configuration dictionary."""
        server_id = str(server_id)
        with self._lock:
            return self.loading["servers"].get(server_id, {}).get("config", None)

    def get_server(self, server_id: Union[int, str]) -> Optional[Dict]:
        """Get complete guild entry dictionary."""
        server_id = str(server_id)
        with self._lock:
            return self.loading["servers"].get(server_id, None)

    def add_channel(self, server_id: Union[int, str], channel_id: Union[int, str]) -> bool:
        """Add channel to authorized discussion list."""
        try:
            server_id = str(server_id)
            channel_id = str(channel_id)
            with self._lock:
                self._ensure_server(server_id)
                channels = self.loading["servers"][server_id]["authorizedChannels"]
                if channel_id in channels:
                    return False
                channels.append(channel_id)
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in add_channel: {error}" + Style.RESET_ALL)
            return False

    def remove_channel(self, server_id: Union[int, str], channel_id: Union[int, str]) -> bool:
        """Remove channel from authorized discussion list."""
        try:
            server_id = str(server_id)
            channel_id = str(channel_id)
            with self._lock:
                channels = self.loading["servers"].get(server_id, {}).get("authorizedChannels", [])
                if channel_id not in channels:
                    return False
                channels.remove(channel_id)
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in remove_channel: {error}" + Style.RESET_ALL)
            return False

    def is_channel_authorized(self, server_id: Union[int, str], channel_id: Union[int, str]) -> bool:
        """Check if channel is authorized for bot interaction."""
        server_id = str(server_id)
        channel_id = str(channel_id)
        with self._lock:
            channels = self.loading["servers"].get(server_id, {}).get("authorizedChannels", [])
            return channel_id in channels

    def get_authorized_channels(self, server_id: Union[int, str]) -> List[str]:
        """Return list of authorized channels."""
        server_id = str(server_id)
        with self._lock:
            return self.loading["servers"].get(server_id, {}).get("authorizedChannels", []).copy()

    def get_all_data(self) -> Dict[str, Any]:
        """Return copy of entire database."""
        with self._lock:
            return self.loading.copy()

    def reload_data(self) -> bool:
        """Force reload database from disk."""
        return self.load_data()

    def reset_database(self) -> bool:
        """Reset database to initial default state."""
        try:
            return self._initialize_database()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in reset_database: {error}" + Style.RESET_ALL)
            return False

    def restore(self, data: dict) -> bool:
        """Restore database state from a dictionary payload."""
        try:
            with self._lock:
                self.loading = data
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE] Error in restore: {error}" + Style.RESET_ALL)
            return False

    def __del__(self):
        if hasattr(self, "_modified") and self._modified:
            self.save_data()


database = Database()