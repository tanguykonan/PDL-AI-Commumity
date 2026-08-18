# ==================================================================================
# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 06/03/2026
# ==================================================================================
import os
import json
import datetime
from typing import Optional
from collections import deque
from app.helps.utils import logger
from settings.config import params


# ==================================================================================
# COUCHE 1 — PROFIL UTILISATEUR
# Structure persistante qui "apprend" l'utilisateur au fil du temps
# ==================================================================================
class UserProfile:
    __slots__ = (
        "user_id", "username", "first_seen", "last_seen",
        "message_count", "preferred_language", "topics",
        "key_facts", "tone_preference", "notes"
    )

    def __init__(self, user_id: str, username: str = ""):
        self.user_id           = user_id
        self.username          = username
        self.first_seen        = datetime.datetime.now().isoformat()
        self.last_seen         = self.first_seen
        self.message_count     = 0
        self.preferred_language= "fr"
        self.topics            = []          # sujets récurrents détectés
        self.key_facts         = []          # faits importants mentionnés
        self.tone_preference   = "neutre"    # décontracté / formel / technique / neutre
        self.notes             = ""          # résumé libre de la relation

    def touch(self, username: str = ""):
        self.last_seen     = datetime.datetime.now().isoformat()
        self.message_count += 1
        if username:
            self.username = username

    def to_dict(self) -> dict:
        return {s: getattr(self, s) for s in self.__slots__}

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        p = cls.__new__(cls)
        for s in cls.__slots__:
            setattr(p, s, data.get(s, []))
        return p

    def to_context_string(self) -> str:
        """Générer un résumé lisible injecté dans le system prompt."""
        parts = [f"Utilisateur : {self.username} (ID {self.user_id})"]
        if self.key_facts:
            parts.append("Faits connus : " + " | ".join(self.key_facts[:5]))
        if self.topics:
            parts.append("Sujets récurrents : " + ", ".join(self.topics[:5]))
        if self.tone_preference != "neutre":
            parts.append(f"Ton préféré : {self.tone_preference}")
        if self.notes:
            parts.append(f"Note : {self.notes}")
        parts.append(f"Messages échangés : {self.message_count}")
        return "\n".join(parts)


# ==================================================================================
# COUCHE 2 — MÉMOIRE UTILISATEUR
# Historique de conversation + profil + résumé de session
# ==================================================================================
class UserMemory:

    def __init__(self, user_id: str, username: str = ""):
        self.user_id     = user_id
        self.history     = deque(maxlen=params.META_USER_LIMIT)
        self.profile     = UserProfile(user_id, username)
        self.summary     = ""
        self.last_active = datetime.datetime.now()
        self.dirty      = False

    def add(self, content: str, role: str = "user", username: str = "") -> int:
        """Ajouter un message. Retourne la taille de l'historique."""
        # Dédoublonnage : on n'ajoute pas si identique au dernier
        if self.history and self.history[-1]["content"] == content:
            return len(self.history)

        self.history.append({"role": role, "content": content})
        self.last_active = datetime.datetime.now()
        self.profile.touch(username)
        self.dirty = True
        return len(self.history)

    def get_recent(self, n: int = params.META_CONTEXT_MESSAGES) -> list:
        """Retourner les N derniers messages."""
        msgs = list(self.history)
        return msgs[-n:] if n > 0 else msgs

    def is_inactive(self, max_hours: float = params.META_INACTIVE_TIME) -> bool:
        delta = (datetime.datetime.now() - self.last_active).total_seconds()
        return delta > max_hours * 3600

    def to_dict(self) -> dict:
        return {
            "user_id"    : self.user_id,
            "history"    : list(self.history),
            "profile"    : self.profile.to_dict(),
            "summary"    : self.summary,
            "last_active": self.last_active.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserMemory":
        obj              = cls.__new__(cls)
        obj.user_id      = data["user_id"]
        obj.history      = deque(data.get("history", []), maxlen=params.META_USER_LIMIT)
        obj.profile      = UserProfile.from_dict(data.get("profile", {"user_id": data["user_id"]}))
        obj.summary      = data.get("summary", "")
        obj.last_active  = datetime.datetime.fromisoformat(data.get("last_active", datetime.datetime.now().isoformat()))
        obj.dirty       = False
        return obj


# ==================================================================================
# COUCHE 3 — MÉMOIRE SERVEUR
# Fil de discussion global (tous utilisateurs confondus sur un serveur)
# ==================================================================================
class ServerMemory:
    """
    Capture le contexte global d'un serveur Discord.
    Chaque entrée du fil contient : auteur, channel, contenu, horodatage.
    Permet au bot de suivre la "vie" du serveur comme Grok suit Twitter/X.
    """

    def __init__(self, server_id: str):
        self.server_id  = server_id
        self.feed       = deque(maxlen=params.META_SERVER_LIMIT)   # fil global
        self.channels   = {}                           # fil par channel : {channel_id: deque}
        self.dirty     = False
        self.last_active = datetime.datetime.now()


    def add(self, author_id: str, author_name: str, channel_id: str,
            channel_name: str, content: str):
        """Enregistre un message dans le fil global et le fil du channel."""
        entry = {
            "author_id"   : str(author_id),
            "author_name" : author_name,
            "channel_id"  : str(channel_id),
            "channel_name": channel_name,
            "content"     : content,
            "ts"          : datetime.datetime.now().isoformat(),
        }
        self.feed.append(entry)

        cid = str(channel_id)
        if cid not in self.channels:
            self.channels[cid] = deque(maxlen=params.META_SERVER_LIMIT // 4)
        self.channels[cid].append(entry)
        self.dirty = True
        self.last_active = datetime.datetime.now()

    def is_inactive(self, max_hours: float = params.META_INACTIVE_TIME) -> bool:
        delta = (datetime.datetime.now() - self.last_active).total_seconds()
        return delta > max_hours * 3600

    def get_recent_feed(self, n: int = params.META_SERVER_INJECT) -> list:
        """Retourne les N derniers messages du fil global."""
        return list(self.feed)[-n:]

    def get_channel_feed(self, channel_id: str, n: int = params.META_SERVER_INJECT) -> list:
        """Retourne les N derniers messages d'un channel."""
        cid = str(channel_id)
        return list(self.channels.get(cid, []))[-n:]

    def to_dict(self) -> dict:
        return {
            "server_id": self.server_id,
            "feed"     : list(self.feed),
            "channels" : {k: list(v) for k, v in self.channels.items()},
            "last_active": self.last_active.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ServerMemory":
        obj            = cls.__new__(cls)
        obj.server_id  = data["server_id"]
        obj.feed       = deque(data.get("feed", []),    maxlen=params.META_SERVER_LIMIT)
        obj.channels   = {
            k: deque(v, maxlen=params.META_SERVER_LIMIT // 4)
            for k, v in data.get("channels", {}).items()
        }
        obj.dirty     = False
        obj.last_active = datetime.datetime.fromisoformat(
            data.get("last_active", datetime.datetime.now().isoformat())
        )
        return obj


# ==================================================================================
# COUCHE 4 — CONTEXT BUILDER
# Fusionne UserMemory + ServerMemory en un bloc de messages prêt pour Groq
# ==================================================================================
class ContextBuilder:
    """
    Construit la liste de messages envoyée à l'API Groq.
    Stratégie :
      1. Injecte le profil utilisateur dans le system prompt
      2. Ajoute un résumé du fil serveur (contexte global)
      3. Ajoute le résumé de session si existant
      4. Ajoute les N derniers messages de l'utilisateur
    """

    @staticmethod
    def build(
            user_mem: UserMemory,
            server_mem: Optional[ServerMemory] = None,
            channel_id: Optional[str] = None,
    ) -> list:

        messages, context_parts = [], []
        context_parts.append(f"━━━ MÉMOIRE UTILISATEUR ━━━\n{user_mem.profile.to_context_string()}")

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
                context_parts.append("━━━ CONTEXTE SERVEUR ━━━\n" + "\n".join(lines))

        if user_mem.summary:
            context_parts.append(f"━━━ RÉSUMÉ ━━━\n{user_mem.summary}")

        if context_parts:
            messages.append({"role": "user", "content": "[CONTEXTE INTERNE]\n" + "\n\n".join(context_parts)})
            messages.append({"role": "assistant", "content": "Contexte reçu."})

        messages.extend(user_mem.get_recent(params.META_CONTEXT_MESSAGES))
        return messages


# ==================================================================================
# ORCHESTRATEUR PRINCIPAL — AdvancedMemory
# Interface unifiée compatible avec l'ancien RandomAccessMemory
# ==================================================================================
class AdvancedMemory:
    """
    ┌─────────────────────────────────────────────────────────┐
    │ ✔ Profils utilisateur persistants (faits, sujets, ton)  │
    │ ✔ Fil global par serveur (contexte partagé)             │
    │ ✔ Fil par channel (conversations localisées)            │
    │ ✔ Résumé automatique des longues sessions               │
    │ ✔ Purge intelligente des inactifs                       │
    │ ✔ Sauvegarde différentielle (dirty flag)                │
    │ ✔ ContextBuilder → prompt optimisé Groq                 │
    │ ✔ Centaines de conversations simultanées                │
    │ ✔ API rétro-compatible RandomAccessMemory v1            │
    └─────────────────────────────────────────────────────────┘
    """

    def __init__(self, memory_path: str = params.META_PATH):
        self.users_path = os.path.join(memory_path, "users")
        self.servers_path = os.path.join(memory_path, "servers/thread")
        self.users      : dict[str, UserMemory]    = {}
        self.servers    : dict[str, ServerMemory]  = {}
        self._ops       : int                      = 0
        self._load()

    # ══════════════════════════════════════════════════════════════════
    # API PUBLIQUE — UTILISATEURS
    # ══════════════════════════════════════════════════════════════════

    def manage(self, user_id: str, message_content: str,
               role: str = "user", username: str = "") -> int:
        """ Ajouter un message dans l'historique utilisateur.
        Retourner la taille de l'historique."""

        uid  = str(user_id)
        umem = self._get_user(uid, username)
        size = umem.add(message_content, role, username)
        self._auto_save()
        return size

    def get_history(self, user_id: str, limit: Optional[int] = None) -> list:
        """Retourner l'historique brut d'un utilisateur."""
        uid  = str(user_id)
        umem = self.users.get(uid)
        if not umem:
            return []
        return umem.get_recent(limit or params.META_CONTEXT_MESSAGES)

    def delete_history(self, user_id: str) -> bool:
        uid = str(user_id)
        if uid in self.users:
            del self.users[uid]
            path = os.path.join(self.users_path, f"{uid}.json")
            if os.path.exists(path):
                os.remove(path)
            return True
        return False

    # ══════════════════════════════════════════════════════════════════
    # API PUBLIQUE — SERVEURS
    # ══════════════════════════════════════════════════════════════════

    def add_server_message(
        self,
        server_id  : str,
        author_id  : str,
        author_name: str,
        channel_id : str,
        channel_name: str,
        content    : str
    ):
        """Enregistre un message dans le fil global du serveur."""
        sid  = str(server_id)
        smem = self._get_server(sid)
        smem.add(str(author_id), author_name, str(channel_id), channel_name, content)
        self._auto_save()

    def get_server_feed(self, server_id: str, n: int = params.META_SERVER_INJECT) -> list:
        """Retourne les N derniers messages du fil global d'un serveur."""
        smem = self.servers.get(str(server_id))
        return smem.get_recent_feed(n) if smem else []

    # ══════════════════════════════════════════════════════════════════
    # API PUBLIQUE — CONTEXTE GROQ
    # ══════════════════════════════════════════════════════════════════

    def build_context(
            self,
            user_id: str,
            server_id: Optional[str] = None,
            channel_id: Optional[str] = None,
            username: str = "",
    ) -> list:
        """
        Construit et retourne la liste de messages prête pour l'API Groq.
        Fusionne : profil user + fil serveur + résumée session + historique récent.
        """
        uid  = str(user_id)
        umem = self._get_user(uid, username)

        smem = self.servers.get(str(server_id)) if server_id else None

        return ContextBuilder.build(
            user_mem     = umem,
            server_mem   = smem,
            channel_id   = str(channel_id) if channel_id else None,
        )

    # ══════════════════════════════════════════════════════════════════
    # API PUBLIQUE — PROFIL UTILISATEUR
    # ══════════════════════════════════════════════════════════════════

    def update_profile(
        self,
        user_id    : str,
        key_facts  : Optional[list]  = None,
        topics     : Optional[list]  = None,
        tone       : Optional[str]   = None,
        notes      : Optional[str]   = None,
        language   : Optional[str]   = None,
    ):
        """
        Met à jour manuellement (ou via IA) le profil d'un utilisateur.
        Peut être appelé après analyse de la réponse Groq.
        """
        uid  = str(user_id)
        umem = self._get_user(uid)

        if key_facts is not None:
            # Fusion sans doublon, max 20 faits
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

        if tone     is not None: umem.profile.tone_preference   = tone
        if notes    is not None: umem.profile.notes              = notes
        if language is not None: umem.profile.preferred_language = language

        umem.dirty = True
        self._auto_save()

    def set_summary(self, user_id: str, summary: str):
        """Injecte un résumé de session (généré par Groq ou manuellement)."""
        uid  = str(user_id)
        umem = self._get_user(uid)
        umem.summary = summary
        umem.dirty  = True
        self._auto_save()

    def should_summarize(self, user_id: str) -> bool:
        """Retourne True si l'historique dépasse le seuil → demander un résumé à Groq."""
        uid  = str(user_id)
        umem = self.users.get(uid)
        return bool(umem and len(umem.history) >= params.META_SUMMARY_THRESHOLD)

    def get_summary_prompt(self, user_id: str) -> Optional[list]:
        """
        Retourne un prompt prêt à envoyer à Groq pour générer un résumé.
        Usage : response = chat.generate_response (memory.get_summary_prompt (user_id))
                memory.set_summary (user_id, response)
                # puis tronquer l'historique
        """
        uid  = str(user_id)
        umem = self.users.get(uid)
        if not umem:
            return None

        history_text = "\n".join(
            f"[{m['role'].upper()}]: {m['content'][:200]}"
            for m in list(umem.history)
        )
        return [
            {"role": "system", "content": (
                "Tu es un assistant de synthèse. "
                "Résume en 5 points clés maximum cette conversation Discord. "
                "Sois concis, factuel, retiens les informations importantes sur l'utilisateur."
            )},
            {"role": "user", "content": f"Conversation à résumer :\n{history_text}"}
        ]

    def trim_after_summary(self, user_id: str, keep_last: int = 10):
        """Après génération d'un résumé, tronque l'historique (garde les N derniers)."""
        uid  = str(user_id)
        umem = self.users.get(uid)
        if umem:
            recent = umem.get_recent(keep_last)
            umem.history = deque(recent, maxlen=params.META_USER_LIMIT)
            umem.dirty  = True

    # ══════════════════════════════════════════════════════════════════
    # API PUBLIQUE — MAINTENANCE
    # ══════════════════════════════════════════════════════════════════

    def clear_memory(self, max_inactive_hours: float = params.META_INACTIVE_TIME) -> int:
        to_remove = [
            uid for uid, umem in self.users.items()
            if umem.is_inactive(max_inactive_hours)
        ]
        for uid in to_remove:
            del self.users[uid]
            path = os.path.join(self.users_path, f"{uid}.json")
            if os.path.exists(path):
                os.remove(path)

        servers_to_remove = [
            sid for sid, smem in self.servers.items()
            if smem.is_inactive(max_inactive_hours)
        ]
        for sid in servers_to_remove:
            del self.servers[sid]
            path = os.path.join(self.servers_path, f"{sid}.json")
            if os.path.exists(path):
                os.remove(path)

        return len(to_remove) + len(servers_to_remove)

    def stats(self) -> dict:
        """Retourner des statistiques sur l'état de la mémoire."""
        return {
            "users_in_memory" : len(self.users),
            "servers_tracked" : len(self.servers),
            "total_messages"  : sum(len(u.history) for u in self.users.values()),
            "total_server_msgs": sum(len(s.feed)   for s in self.servers.values()),
        }

    def save_to_file(self) -> bool:
        """[Rétro-compatible v1] Force la sauvegarde."""
        return self._save()

    # ══════════════════════════════════════════════════════════════════
    # INTERNES
    # ══════════════════════════════════════════════════════════════════

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
        """Sauvegarde différentielle : toutes les SAVE_EVERY opérations."""
        self._ops += 1
        if self._ops >= params.META_SAVE_EVERY:
            self._save()
            self._ops = 0

    def _save(self) -> bool:
        try:
            os.makedirs(self.users_path, exist_ok=True)
            os.makedirs(self.servers_path, exist_ok=True)

            # Sauvegarde des utilisateurs dirty uniquement
            for uid, umem in self.users.items():
                if umem.dirty:
                    path = os.path.join(self.users_path, f"{uid}.json")
                    tmp = path + ".tmp"
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump(umem.to_dict(), f, ensure_ascii=False, indent=2)
                    os.replace(tmp, path)
                    umem.dirty = False

            # Sauvegarde des serveurs dirty uniquement
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
            logger.error(f"[MEMORY v2]-> Erreur sauvegarde: {e}", exc_info=True)
            return False

    def _load(self) -> bool:
        try:
            os.makedirs(self.users_path, exist_ok=True)
            os.makedirs(self.servers_path, exist_ok=True)

            # Chargement des utilisateurs
            for filename in os.listdir(self.users_path):
                if filename.endswith(".json"):
                    uid = filename[:-5]  # retire ".json"
                    path = os.path.join(self.users_path, filename)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            self.users[uid] = UserMemory.from_dict(json.load(f))
                    except (json.JSONDecodeError, KeyError) as err:
                        logger.error(f"[ERROR DDR2]-> Fichier user corrompu ignoré ({filename}): {err}", exc_info=True)
                        continue

            # Chargement des serveurs
            for filename in os.listdir(self.servers_path):
                if filename.endswith(".json"):
                    sid = filename[:-5]
                    path = os.path.join(self.servers_path, filename)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            self.servers[sid] = ServerMemory.from_dict(json.load(f))
                    except (json.JSONDecodeError, KeyError) as err:
                        logger.error(f"[ERROR DDR2]-> Fichier user corrompu ignoré ({filename}): {err}", exc_info=True)
                        continue

            return True
        except Exception as e:
            logger.error(f"[ERROR DDR2]-> Erreur chargement: {e}", exc_info=True)
            return False

    def __del__(self):
        dirty = any(u.dirty for u in self.users.values()) or \
                any(s.dirty for s in self.servers.values())  # ← manquait
        if dirty:
            self._save()


# ==================================================================================
# ALIAS RÉTRO-COMPATIBLE — permet de remplacer RandomAccessMemory sans rien casser
# ==================================================================================
RandomAccessMemory = AdvancedMemory
