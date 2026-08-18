# ==================================================================================
# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 30/12/2025
# ==================================================================================
import os
import json
import datetime
from app.helps.utils import logger
from settings.config import params
meta_path = os.path.join(params.META_PATH, "meta.json") # à éditer si je veux le réutiliser

class RandomAccessMemory:
    def __init__(self, memory_limit = params.META_LIMIT):
        try:
            self.memory_limit = memory_limit
            self.memory = {}
            self.lastMessageTime = {}
            self.modified = False
            self.load_from_file()
        except Exception as error:
            logger.error(f'[MEMORY ERROR]-> Erreur de la fonction __init__ de la ddr: {error}', exc_info=True)
            print(f'[MEMORY ERROR]-> [MEMORY ERROR]=> Erreur de la fonction __init__ de la ddr: {error}')

    def clear_memory(self, max_inactive_time = params.META_INACTIVE_TIME * 3600):
        try:
            now = datetime.datetime.now()
            to_remove = []

            for user_id, lastTime in self.lastMessageTime.items():
                if (now - lastTime).total_seconds() > max_inactive_time:
                    to_remove.append(user_id)

            for userID in to_remove:
                self.memory.pop(userID, None)
                self.lastMessageTime.pop(userID, None)
                self.modified = True

            if self.modified:
                self.save_to_file()

            return len(to_remove)
        except Exception as error:
            logger.error(f'[MEMORY ERROR]-> Erreur du néttoyage de la memoire: {error}', exc_info=True)
            print(f'[MEMORY ERROR]-> Erreur du néttoyage de la memoire: {error}')

    def manage(self, user_id, message_content, role = 'user'):
        """Gestionnaire des ajouts dans la session d'un utilisateur"""
        try:
            user_id= str(user_id)
            if user_id not in self.memory:
                self.memory[user_id] = []

            message = {
                'role': role,
                'content': message_content
            }

            if not self.memory[user_id] or self.memory[user_id][-1]['content'] != message_content:
                self.memory[user_id].append(message)
                self.modified = True

            self.lastMessageTime[user_id] = datetime.datetime.now()

            if 0 < self.memory_limit < len(self.memory[user_id]):
                self.memory[user_id] = self.memory[user_id][-self.memory_limit:]
                self.modified = True

            if self.modified and len(self.memory[user_id]) %5 == 0:
                self.save_to_file()

            return len(self.memory[user_id])
        except Exception as error:
            logger.error(f'[MEMORY ERROR]-> Erreur lors de la gestion des ajouts dans la session d\'un utilisateur: {error}', exc_info=True)
            print(f'[MEMORY ERROR]-> Erreur lors de la gestion des ajouts dans la session d\'un utilisateur: {error}')

    def get_history(self, user_id, limit = None):
        """Récupérer l'historique d'un utilisateur (limit = None)"""
        try:
            user_id= str(user_id)
            history = self.memory.get(user_id, [])
            if limit and limit > 0:
                history = history[-limit:]
            return history
        except Exception as error:
            logger.error(f'[MEMORY ERROR]-> Erreur de recuperation de l\'historique d\'un utilisateur: {error}', exc_info=True)
            print(f'[MEMORY ERROR]-> Erreur de recuperation de l\'historique d\'un utilisateur: {error}')
            return []

    def delete_history(self, user_id):
        """Supprimer l'historique de la session d'un utilisateur"""
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
            logger.error(f'[MEMORY ERROR]-> Échec de la supprimer l\'historique de la session d\'un utilisateur: {error}', exc_info=True)
            print(f'[MEMORY ERROR]-> Échec de la supprimer l\'historique de la session d\'un utilisateur:{error}')
            return False

    def save_to_file(self):
        """Sauvegarde les informations de la memoire ram dans la rom"""
        try:
            os.makedirs(os.path.dirname(meta_path), exist_ok=True)
            data = {
                'conversations': self.memory,
                'lastMessageTime': {k: v.isoformat() for k, v in self.lastMessageTime.items()}
            }

            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            self.modified = False
            return True
        except Exception as error:
            logger.error(f'[MEMORY ERROR]-> Erreur de sauge garde des formations en ram dans la rom: {error}', exist_ok=True)
            print(f'[MEMORY ERROR]-> Erreur de sauge garde des formations en ram dans la rom: {error}')
            return False

    def load_from_file(self):
        """Chargement des informations de la rom dans la memoire ram"""
        try:
            if not os.path.exists(meta_path):
                os.makedirs(os.path.dirname(meta_path), exist_ok=True)
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump({"conversations": {}, "lastMessageTime": {}}, f)
                    return  True

            with open(meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.memory = data.get("conversations", {})
                self.lastMessageTime = {
                    k: datetime.datetime.fromisoformat(v)
                    for k, v in data.get("lastMessageTime", {}).items()
                }
            return True
        except json.decoder.JSONDecodeError as e:
            logger.error(f'[MEMORY ERROR]=> ', e)
            print(f'[MEMORY ERROR]=> {e}')
            self.memory = {}
            self.lastMessageTime = {}
            self.save_to_file()
            return False
        except Exception as error:
            logger.error(f'[MEMORY ERROR]-> Erreur lors du chargement des informations en rom dans la ram: {error}', exc_info=True)
            print(f'[MEMORY ERROR]-> Erreur lors du chargement des informations en rom dans la ram: {error}')
            return False

    def __del__(self):
        """Sauvegarde finale lorsque les objets de la session d'un utilisateur sont détruits"""
        if self.modified:
            self.save_to_file()