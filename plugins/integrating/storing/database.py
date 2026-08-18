# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 30/12/2025
# Mise à jour: 17/04/2026
# ==================================================================================
import os
import json
import threading
from colorama import Fore, Style
from settings.config import params
from typing import List, Dict, Any, Optional, Union


class Database:

    def __init__(self, data_path: str = params.DATABASE_PATH):
        self.data = data_path
        self._lock = threading.RLock()
        self._modified = False
        self.loading = self._get_default_structure()
        if not self.load_data():
            print(Fore.YELLOW + "[WARNING DATABASE]-> Utilisation de la structure par défaut." + Style.RESET_ALL)

    # ==================================================================================
    # ================================ STRUCTURE =======================================
    # ==================================================================================

    @staticmethod
    def _get_default_structure() -> Dict[str, Any]:
        return {
            "bot": {
                "admins": [1233020939898327092, 767678057770385438],
                "activities": [],
                "stats": {
                    "userNumber": 4558,
                    "serverNumber": 7,
                    "queryNumber": 5600,
                    "usersInMemory": 0,
                    "serversTracked": 0,
                    "totalMessages": 0,
                    "totalServerMessages": 0
                }
            },
            "users": {},
            "servers": {}
        }

    @staticmethod
    def _get_default_user() -> Dict[str, Any]:
        return {
            "isBanned": False
        }

    @staticmethod
    def _get_default_server() -> Dict[str, Any]:
        return {
            "isBanned": False,
            "isPremium": False,
            "config": {
                "language": "fr",
                "mode": "default",
                "alertChannel": None,
                "autoSanction": "Aucune sanction"
            },
            "authorizedChannels": []
        }

    # ==================================================================================
    # ================================ CHARGEMENT / SAUVEGARDE =========================
    # ==================================================================================

    def load_data(self) -> bool:
        try:
            if not os.path.exists(self.data) or os.path.getsize(self.data) == 0:
                return self._initialize_database()

            with self._lock:
                with open(self.data, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)

                default_structure = self._get_default_structure()
                self.loading = self._merge_structures(default_structure, loaded_data)

            return True

        except json.JSONDecodeError as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Le fichier db.json est corrompu. Il sera initialisé: {error}" + Style.RESET_ALL)
            return self._initialize_database()

        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite lors du chargement de db.json: {error}" + Style.RESET_ALL)
            return False

    @staticmethod
    def _merge_structures(default: Dict, loaded: Dict) -> Dict:
        """Fusionner la structure par défaut avec les données chargées"""
        #== Ajoute les clés manquantes sans écraser les données existantes ==#

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
        """Initialiser une nouvelle base de données avec la structure par défaut"""
        try:
            with self._lock:
                self.loading = self._get_default_structure()
                self._modified = True
            self.save_data()
            return True
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite lors de l'initialisation: {error}" + Style.RESET_ALL)
            return False

    def save_data(self) -> bool:
        """Sauvegarder les données dans le fichier JSON de manière atomique"""
        tmp_path = f"{self.data}.tmp"
        try:
            with self._lock:
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    json.dump(self.loading, f, indent=4, ensure_ascii=False)

                if os.name == 'nt':
                    if os.path.exists(self.data):
                        os.remove(self.data)
                    os.rename(tmp_path, self.data)
                else:
                    os.replace(tmp_path, self.data)

                self._modified = False

            return True

        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite lors de la sauvegarde: {error}" + Style.RESET_ALL)
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception as error:
                    print(Fore.YELLOW + f"[WARNING DATABASE]-> La suppression du fichier temporaire {tmp_path} a échouée: {error}" + Style.RESET_ALL)
            return False

    # ==================================================================================
    # ================================ BOT — ADMINS ====================================
    # ==================================================================================

    def add_admin(self, user_id: Union[int, str]) -> bool:
        try:
            with self._lock:
                if user_id in self.loading["bot"]["admins"]:
                    return False
                self.loading["bot"]["admins"].append(user_id)
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [add_admin]: {error}" + Style.RESET_ALL)
            return False

    def remove_admin(self, user_id: Union[int, str]) -> bool:
        try:
            with self._lock:
                if user_id not in self.loading["bot"]["admins"]:
                    return False
                self.loading["bot"]["admins"].remove(user_id)
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [remove_admin]: {error}" + Style.RESET_ALL)
            return False

    def is_admin(self, user_id: Union[int, str]) -> bool:
        # BUG FIX: Normaliser en int des deux côtés pour éviter les échecs silencieux
        # quand user_id arrive en str (ex: depuis une commande slash ou un ID JSON).
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return False
        with self._lock:
            return uid in [int(a) for a in self.loading["bot"]["admins"]]

    # ==================================================================================
    # ================================ BOT — ACTIVITIES ================================
    # ==================================================================================

    def add_activity(self, activity: str) -> bool:
        try:
            with self._lock:
                if activity in self.loading["bot"]["activities"]:
                    return False
                self.loading["bot"]["activities"].append(activity)
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [add_activity]: {error}" + Style.RESET_ALL)
            return False

    def remove_activity(self, activity: str) -> bool:
        try:
            with self._lock:
                if activity not in self.loading["bot"]["activities"]:
                    return False
                self.loading["bot"]["activities"].remove(activity)
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [remove_activity]: {error}" + Style.RESET_ALL)
            return False

    def get_activities(self) -> List[str]:
        with self._lock:
            return self.loading["bot"]["activities"].copy()

    # ==================================================================================
    # ================================ BOT — STATS =====================================
    # ==================================================================================

    def update_stat(self, stat_key: str, value: int) -> bool:
        """Mettre à jour une statistique du bot"""
        try:
            with self._lock:
                if stat_key not in self.loading["bot"]["stats"]:
                    print(Fore.YELLOW + f"[WARNING DATABASE]-> La clé '{stat_key}' est inexistante dans le système de la methode [update_stat]" + Style.RESET_ALL)
                    return False
                self.loading["bot"]["stats"][stat_key] = value
                self._modified = True
            self.save_data()
            return True
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [update_stat]: {error}" + Style.RESET_ALL)
            return False

    def increment_stat(self, stat_key: str, increment: int = 1) -> bool:
        try:
            with self._lock:
                if stat_key not in self.loading["bot"]["stats"]:
                    print(Fore.YELLOW + f"[WARNING DATABASE]-> La clé '{stat_key}' est inexistante dans le système de la methode [increment_stat]" + Style.RESET_ALL)
                    return False
                current = self.loading["bot"]["stats"][stat_key]
            return self.update_stat(stat_key, current + increment)
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [increment_stat]: {error}" + Style.RESET_ALL)
            return False

    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            return self.loading["bot"]["stats"].copy()

    # ==================================================================================
    # ================================ UTILISATEURS ====================================
    # ==================================================================================

    def _ensure_user(self, user_id: Union[int, str]) -> None:
        """Créer l'entrée utilisateur si elle n'existe pas"""
        if user_id not in self.loading["users"]:
            self.loading["users"][user_id] = self._get_default_user()

    def ban_user(self, user_id: Union[int, str]) -> bool:
        try:
            user_id = str(user_id)
            with self._lock:
                self._ensure_user(user_id)
                self.loading["users"][user_id]["isBanned"] = True
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [ban_user]: {error}" + Style.RESET_ALL)
            return False

    def unban_user(self, user_id: Union[int, str]) -> bool:
        try:
            user_id = str(user_id)
            with self._lock:
                self._ensure_user(user_id)
                self.loading["users"][user_id]["isBanned"] = False
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [unban_user]: {error}" + Style.RESET_ALL)
            return False

    def is_user_banned(self, user_id: Union[int, str]) -> bool:
        user_id = str(user_id)
        with self._lock:
            return self.loading["users"].get(user_id, {}).get("isBanned", False)

    def get_user(self, user_id: Union[int, str]) -> Optional[Dict]:
        user_id = str(user_id)
        with self._lock:
            return self.loading["users"].get(user_id, None)

    # ==================================================================================
    # ================================ SERVEURS ========================================
    # ==================================================================================

    def _ensure_server(self, server_id: Union[int, str]) -> None:
        """Créer l'entrée serveur si elle n'existe pas"""
        if server_id not in self.loading["servers"]:
            self.loading["servers"][server_id] = self._get_default_server()

    def ban_server(self, server_id: Union[int, str]) -> bool:
        try:
            server_id = str(server_id)
            with self._lock:
                self._ensure_server(server_id)
                self.loading["servers"][server_id]["isBanned"] = True
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [ban_server]: {error}" + Style.RESET_ALL)
            return False

    def unban_server(self, server_id: Union[int, str]) -> bool:
        try:
            server_id = str(server_id)
            with self._lock:
                self._ensure_server(server_id)
                self.loading["servers"][server_id]["isBanned"] = False
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [unban_server]: {error}" + Style.RESET_ALL)
            return False

    def is_server_banned(self, server_id: Union[int, str]) -> bool:
        server_id = str(server_id)
        with self._lock:
            return self.loading["servers"].get(server_id, {}).get("isBanned", False)

    def set_premium(self, server_id: Union[int, str], state: bool = True) -> bool:
        try:
            server_id = str(server_id)
            with self._lock:
                self._ensure_server(server_id)
                self.loading["servers"][server_id]["isPremium"] = state
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [set_premium]: {error}" + Style.RESET_ALL)
            return False

    def is_server_premium(self, server_id: Union[int, str]) -> bool:
        server_id = str(server_id)
        with self._lock:
            return self.loading["servers"].get(server_id, {}).get("isPremium", False)

    # ==================================================================================
    # ================================ SERVEURS — CONFIG ===============================
    # ==================================================================================

    def set_server_config(self, server_id: Union[int, str], key: str, value: Any) -> bool:
        """Mettre à jour une clé de configuration d'un serveur"""
        try:
            server_id = str(server_id)
            with self._lock:
                self._ensure_server(server_id)
                self.loading["servers"][server_id]["config"][key] = value
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [set_server_config]: {error}" + Style.RESET_ALL)
            return False

    def get_server_config(self, server_id: Union[int, str]) -> Optional[Dict]:
        server_id = str(server_id)
        with self._lock:
            return self.loading["servers"].get(server_id, {}).get("config", None)

    def get_server(self, server_id: Union[int, str]) -> Optional[Dict]:
        server_id = str(server_id)
        with self._lock:
            return self.loading["servers"].get(server_id, None)

    # ==================================================================================
    # ================================ SERVEURS — CANAUX ===============================
    # ==================================================================================

    def add_channel(self, server_id: Union[int, str], channel_id: Union[int, str]) -> bool:
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
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [add_channel]: {error}" + Style.RESET_ALL)
            return False

    def remove_channel(self, server_id: Union[int, str], channel_id: Union[int, str]) -> bool:
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
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [remove_channel]: {error}" + Style.RESET_ALL)
            return False

    def is_channel_authorized(self, server_id: Union[int, str], channel_id: Union[int, str]) -> bool:
        server_id = str(server_id)
        channel_id = str(channel_id)
        with self._lock:
            channels = self.loading["servers"].get(server_id, {}).get("authorizedChannels", [])
            return channel_id in channels

    def get_authorized_channels(self, server_id: Union[int, str]) -> List[str]:
        """Retourner la liste des canaux autorisés d'un serveur"""
        server_id = str(server_id)
        with self._lock:
            return self.loading["servers"].get(server_id, {}).get("authorizedChannels", []).copy()

    # ==================================================================================
    # ================================ UTILITAIRES =====================================
    # ==================================================================================

    def get_all_data(self) -> Dict[str, Any]:
        with self._lock:
            return self.loading.copy()

    def reload_data(self) -> bool:
        """Forcer le rechargement des données depuis le fichier"""
        return self.load_data()

    def reset_database(self) -> bool:
        try:
            return self._initialize_database()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [reset_database]: {error}" + Style.RESET_ALL)
            return False

    def restore(self, data: dict) -> bool:
        """Restaurer les données depuis une sauvegarde externe"""
        try:
            with self._lock:
                self.loading = data
                self._modified = True
            return self.save_data()
        except Exception as error:
            print(Fore.RED + f"[ERROR DATABASE]-> Une erreur s'est produite au niveau de la methode [restore]: {error}" + Style.RESET_ALL)
            return False

    """
    def backup(self, backup_path: Optional[str] = None) -> bool:
        #Créer une sauvegarde de la base de données
        try:
            if not backup_path:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{self.data}.backup_{timestamp}"

            with self._lock:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(self.loading, f, indent=4, ensure_ascii=False)

            return True

        except Exception as error:
            print(f"[ERROR DATABASE]-> Erreur backup: {error}")
            return False
    """

    def __del__(self):
        """Sauvegarde finale lors de la destruction de l'objet"""
        if hasattr(self, '_modified') and self._modified:
            self.save_data()


database = Database()