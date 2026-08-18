# ==================================================================================
# ============================ GESTIONNAIRE D'OUTILS IA ============================
# ==================================================================================
import json
import asyncio
import discord
from discord.ext import commands
from app.helps.utils import logger
from plugins.processing.agenticRag.wse import WebSearchEngine
from plugins.processing.agenticRag.ise import InternalSearchEngine

class AIToolManager:
    def __init__(self, bot: commands.Bot, message: discord.Message):
        self.bot = bot
        self.message = message
        self.wse = WebSearchEngine()
        self.ise = InternalSearchEngine()
        
    def get_tools(self, server_id: str = "") -> list:
        """Retourne la liste des outils (Function Calling) disponibles selon le contexte."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Effectue une recherche sur internet pour trouver des informations récentes, d'actualité ou des connaissances générales.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "La requête de recherche optimisée (ex: 'dernières nouvelles IA 2026')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_server_stats",
                    "description": "Obtenir les statistiques en temps réel du serveur actuel (membres, nom, date de création, etc.).",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_user_info",
                    "description": "Obtenir des informations sur l'utilisateur qui parle (rôles, id, nom).",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "play_music",
                    "description": "Jouer de la musique dans le salon vocal de l'utilisateur. Appelle cette fonction quand on te demande de mettre de la musique.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Le nom de la musique ou l'artiste à rechercher (ex: 'Daft Punk Get Lucky')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "stop_music",
                    "description": "Arrêter la musique en cours, vider la file d'attente et déconnecter le bot du salon vocal.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "pause_music",
                    "description": "Mettre en pause la musique en cours de lecture.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "resume_music",
                    "description": "Reprendre la lecture de la musique mise en pause.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "skip_music",
                    "description": "Passer à la musique suivante dans la file d'attente.",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

        if server_id:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": "internal_rag_search",
                        "description": "Recherche dans la base de données interne du serveur (historique, logs ou contexte spécifique de la communauté).",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Ce qu'il faut chercher dans les logs ou le contexte interne."
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }
            )

        return tools

    async def execute_tool(self, tool_call, last_user_msg: str, server_id: str = None) -> dict:
        """Exécute l'outil demandé par le modèle et retourne le résultat formaté pour l'API."""
        func_name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            args = {}
            
        tool_result = "Aucun résultat."
        try:
            if func_name == "web_search":
                tool_result = await self._web_search(args, last_user_msg)
            elif func_name == "internal_rag_search" and server_id:
                tool_result = await self._internal_rag_search(args, last_user_msg, server_id)
            elif func_name == "get_server_stats":
                tool_result = self._get_server_stats()
            elif func_name == "get_user_info":
                tool_result = self._get_user_info()
            elif func_name == "play_music":
                tool_result = await self._play_music(args)
            elif func_name == "stop_music":
                tool_result = await self._stop_music()
            elif func_name == "pause_music":
                tool_result = await self._pause_music()
            elif func_name == "resume_music":
                tool_result = await self._resume_music()
            elif func_name == "skip_music":
                tool_result = await self._skip_music()
            else:
                tool_result = f"Erreur : L'outil {func_name} n'existe pas ou n'est pas autorisé ici."
                
        except Exception as e:
            logger.error(f"[ERROR AITOOLS]-> Erreur exécution outil {func_name}: {e}", exc_info=True)
            tool_result = f"Erreur lors de l'exécution de l'outil: {str(e)}"
        
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": func_name,
            "content": str(tool_result)
        }

    # ==================================================================================
    # IMPLÉMENTATION DES OUTILS
    # ==================================================================================

    async def _web_search(self, args: dict, last_user_msg: str) -> str:
        query = args.get("query", last_user_msg)
        res = await self.wse.search(query)
        return res if res else "Aucun résultat pertinent trouvé sur le web."

    async def _internal_rag_search(self, args: dict, last_user_msg: str, server_id: str) -> str:
        query = args.get("query", last_user_msg)
        res = await self.ise.call_rag_analyzer(query, server_id)
        return res if (res and res.strip().lower() != "ras") else "RAS (Rien de pertinent trouvé dans la base de données interne)."

    def _get_server_stats(self) -> str:
        guild = self.message.guild
        if guild:
            created_at = guild.created_at.strftime('%d/%m/%Y') if guild.created_at else "Inconnue"
            return f"Serveur: {guild.name}, Membres: {guild.member_count}, Créé le: {created_at}"
        return "Information indisponible (la conversation n'est pas sur un serveur)."

    def _get_user_info(self) -> str:
        author = self.message.author
        if hasattr(author, 'roles'):
            roles = ", ".join([r.name for r in author.roles if r.name != "@everyone"])
        else:
            roles = "Aucun"
        return f"Utilisateur: {author.display_name}, ID: {author.id}, Rôles: {roles if roles else 'Aucun'}"

    async def _play_music(self, args: dict) -> str:
        query = args.get("query")
        if not query:
            return "Échec : Aucune requête musicale fournie."
            
        author = self.message.author
        guild = self.message.guild
        voice = getattr(author, "voice", None)
        
        if not voice or not voice.channel:
            return "Échec : Impossible de mettre de la musique, l'utilisateur n'est pas dans un salon vocal."

        music_cog = self.bot.get_cog("music")
        if not music_cog or not getattr(music_cog, "lavalink_manager", None) or not music_cog.lavalink_manager.is_initialized:
            return "Échec : Le système de musique Lavalink n'est pas prêt."
            
        try:
            voice_channel = voice.channel
            client = music_cog.lavalink_manager.client
            
            # Créer/Récupérer le player Lavalink
            client.player_manager.create(guild.id)
            player = client.player_manager.get(guild.id)
            player.store('channel', self.message.channel.id)
            
            # Connecter le bot au salon vocal (s'il n'y est pas)
            if not guild.voice_client or getattr(guild.voice_client.channel, "id", None) != voice_channel.id:
                if guild.voice_client:
                    await guild.voice_client.disconnect(force=True)
                    await asyncio.sleep(0.3)
                
                from plugins.integrating.hosting.node_lavalink import LavalinkVoiceClient
                await voice_channel.connect(cls=LavalinkVoiceClient)
            
            player.channel_id = str(voice_channel.id)
            
            # Chercher la musique
            search = query if query.startswith(("ytsearch:", "http://", "https://")) else f"ytsearch:{query}"
            results = await player.node.get_tracks(search)
            
            if not results or not results.tracks:
                return f"Échec : Aucune musique trouvée pour '{query}'."

            # Ajouter et Jouer
            track = results.tracks[0]
            player.add(requester=author.id, track=track)
            if not player.is_playing:
                await player.play()
            return f"Succès : La musique '{track.title}' a été trouvée et lancée dans le salon vocal."
                
        except Exception as e:
            logger.error(f"[ERROR AITOOLS]-> Erreur lors de la lecture musicale via Tool: {e}", exc_info=True)
            return f"Échec interne lors du lancement de la musique : {e}"

    async def _stop_music(self) -> str:
        guild = self.message.guild
        if not guild:
            return "Échec : Action impossible hors d'un serveur."
            
        music_cog = self.bot.get_cog("music")
        if not music_cog or not getattr(music_cog, "lavalink_manager", None) or not music_cog.lavalink_manager.is_initialized:
            return "Échec : Le système de musique Lavalink n'est pas prêt."
            
        try:
            player = await music_cog.lavalink_manager.get_player(guild)
            if not player:
                return "Je ne joue aucune musique actuellement."
                
            player.queue.clear()
            await player.stop()
            success = await music_cog.lavalink_manager.disconnect_player(guild)
            
            if success:
                return "Succès : La musique a été arrêtée et le lecteur déconnecté."
            else:
                return "La musique est arrêtée mais une erreur est survenue lors de la déconnexion."
        except Exception as e:
            logger.error(f"[ERROR AITOOLS]-> Erreur stop_music via Tool: {e}", exc_info=True)
            return f"Échec lors de l'arrêt de la musique : {e}"

    async def _pause_music(self) -> str:
        guild = self.message.guild
        if not guild:
            return "Échec : Action impossible hors d'un serveur."
            
        music_cog = self.bot.get_cog("music")
        if not music_cog or not getattr(music_cog, "lavalink_manager", None) or not music_cog.lavalink_manager.is_initialized:
            return "Échec : Le système de musique Lavalink n'est pas prêt."
            
        try:
            player = await music_cog.lavalink_manager.get_player(guild)
            if not player or not player.is_playing:
                return "Aucune musique n'est en cours de lecture."
                
            if player.paused:
                return "La musique est déjà en pause."
                
            await player.set_pause(True)
            return "Succès : La musique a été mise en pause."
        except Exception as e:
            logger.error(f"[ERROR AITOOLS]-> Erreur pause_music via Tool: {e}", exc_info=True)
            return f"Échec de la mise en pause : {e}"

    async def _resume_music(self) -> str:
        guild = self.message.guild
        if not guild:
            return "Échec : Action impossible hors d'un serveur."
            
        music_cog = self.bot.get_cog("music")
        if not music_cog or not getattr(music_cog, "lavalink_manager", None) or not music_cog.lavalink_manager.is_initialized:
            return "Échec : Le système de musique Lavalink n'est pas prêt."
            
        try:
            player = await music_cog.lavalink_manager.get_player(guild)
            if not player:
                return "Aucun lecteur n'est actif."
                
            if not player.paused:
                return "La musique n'est pas en pause actuellement."
                
            await player.set_pause(False)
            return "Succès : La lecture de la musique a repris."
        except Exception as e:
            logger.error(f"[ERROR AITOOLS]-> Erreur resume_music via Tool: {e}", exc_info=True)
            return f"Échec de la reprise de la musique : {e}"

    async def _skip_music(self) -> str:
        guild = self.message.guild
        if not guild:
            return "Échec : Action impossible hors d'un serveur."
            
        music_cog = self.bot.get_cog("music")
        if not music_cog or not getattr(music_cog, "lavalink_manager", None) or not music_cog.lavalink_manager.is_initialized:
            return "Échec : Le système de musique Lavalink n'est pas prêt."
            
        try:
            player = await music_cog.lavalink_manager.get_player(guild)
            if not player or not player.is_playing:
                return "Aucune musique n'est en cours de lecture à passer."
                
            await player.skip()
            return "Succès : Musique passée. Lecture de la piste suivante."
        except Exception as e:
            logger.error(f"[ERROR AITOOLS]-> Erreur skip_music via Tool: {e}", exc_info=True)
            return f"Échec lors du passage à la musique suivante : {e}"
