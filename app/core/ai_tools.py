"""Function calling definitions and execution engine for autonomous AI tools."""

import json
import asyncio
import discord
from discord.ext import commands
from app.helps.utils import logger
from plugins.processing.agenticRag.wse import WebSearchEngine
from plugins.processing.agenticRag.ise import InternalSearchEngine


class AIToolManager:
    """Manages AI tool specifications and executes function calls requested by the LLM."""

    def __init__(self, bot: commands.Bot, message: discord.Message):
        self.bot = bot
        self.message = message
        self.wse = WebSearchEngine()
        self.ise = InternalSearchEngine()

    def get_tools(self, server_id: str = "") -> list:
        """Return the schema of available function calling tools based on current context."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Perform an internet search to find up-to-date facts, news, or general knowledge.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query (e.g. 'latest AI news 2026').",
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_server_stats",
                    "description": "Get real-time statistics of the current Discord server (member count, name, creation date).",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_user_info",
                    "description": "Get information about the user currently speaking (roles, id, display name).",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "play_music",
                    "description": "Play music in the user's voice channel. Call this function when the user asks to play a song.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Song title or artist to search (e.g. 'Daft Punk Get Lucky').",
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "stop_music",
                    "description": "Stop current music playback, clear queue, and disconnect from voice channel.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "pause_music",
                    "description": "Pause current music playback.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "resume_music",
                    "description": "Resume paused music playback.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "skip_music",
                    "description": "Skip to the next song in the music queue.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]

        if server_id:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": "internal_rag_search",
                        "description": "Search local server logs and contextual history for server-specific topics.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "What to look for in the server logs.",
                                }
                            },
                            "required": ["query"],
                        },
                    },
                }
            )

        return tools

    async def execute_tool(self, tool_call, last_user_msg: str, server_id: str = None) -> dict:
        """Execute the requested tool and format the result for the LLM API payload."""
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
            logger.error(f"[ERROR AITOOLS] Failed to execute tool {func_name}: {e}", exc_info=True)
            tool_result = f"Erreur lors de l'exécution de l'outil: {str(e)}"

        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": func_name,
            "content": str(tool_result),
        }

    async def _web_search(self, args: dict, last_user_msg: str) -> str:
        """Execute web search via Tavily API."""
        query = args.get("query", last_user_msg)
        res = await self.wse.search(query)
        return res if res else "Aucun résultat pertinent trouvé sur le web."

    async def _internal_rag_search(self, args: dict, last_user_msg: str, server_id: str) -> str:
        """Execute local server log context search."""
        query = args.get("query", last_user_msg)
        res = await self.ise.call_rag_analyzer(query, server_id)
        return res if (res and res.strip().lower() != "ras") else "RAS (Rien de pertinent trouvé dans la base de données interne)."

    def _get_server_stats(self) -> str:
        """Get live server metrics."""
        guild = self.message.guild
        if guild:
            created_at = guild.created_at.strftime("%d/%m/%Y") if guild.created_at else "Inconnue"
            return f"Serveur: {guild.name}, Membres: {guild.member_count}, Créé le: {created_at}"
        return "Information indisponible (la conversation n'est pas sur un serveur)."

    def _get_user_info(self) -> str:
        """Get author metadata and roles."""
        author = self.message.author
        if hasattr(author, "roles"):
            roles = ", ".join([r.name for r in author.roles if r.name != "@everyone"])
        else:
            roles = "Aucun"
        return f"Utilisateur: {author.display_name}, ID: {author.id}, Rôles: {roles if roles else 'Aucun'}"

    async def _play_music(self, args: dict) -> str:
        """Connect to voice and enqueue song track."""
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

            client.player_manager.create(guild.id)
            player = client.player_manager.get(guild.id)
            player.store("channel", self.message.channel.id)

            if not guild.voice_client or getattr(guild.voice_client.channel, "id", None) != voice_channel.id:
                if guild.voice_client:
                    await guild.voice_client.disconnect(force=True)
                    await asyncio.sleep(0.3)

                from plugins.integrating.hosting.node_lavalink import LavalinkVoiceClient

                await voice_channel.connect(cls=LavalinkVoiceClient)

            player.channel_id = str(voice_channel.id)

            search = query if query.startswith(("ytsearch:", "http://", "https://")) else f"ytsearch:{query}"
            results = await player.node.get_tracks(search)

            if not results or not results.tracks:
                return f"Échec : Aucune musique trouvée pour '{query}'."

            track = results.tracks[0]
            player.add(requester=author.id, track=track)
            if not player.is_playing:
                await player.play()
            return f"Succès : La musique '{track.title}' a été trouvée et lancée dans le salon vocal."

        except Exception as e:
            logger.error(f"[ERROR AITOOLS] Failed to play music via tool: {e}", exc_info=True)
            return f"Échec interne lors du lancement de la musique : {e}"

    async def _stop_music(self) -> str:
        """Stop music and disconnect."""
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
            return "La musique est arrêtée mais une erreur est survenue lors de la déconnexion."
        except Exception as e:
            logger.error(f"[ERROR AITOOLS] Error in _stop_music: {e}", exc_info=True)
            return f"Échec lors de l'arrêt de la musique : {e}"

    async def _pause_music(self) -> str:
        """Pause playback."""
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
            logger.error(f"[ERROR AITOOLS] Error in _pause_music: {e}", exc_info=True)
            return f"Échec de la mise en pause : {e}"

    async def _resume_music(self) -> str:
        """Resume playback."""
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
            logger.error(f"[ERROR AITOOLS] Error in _resume_music: {e}", exc_info=True)
            return f"Échec de la reprise de la musique : {e}"

    async def _skip_music(self) -> str:
        """Skip current track."""
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
            logger.error(f"[ERROR AITOOLS] Error in _skip_music: {e}", exc_info=True)
            return f"Échec lors du passage à la musique suivante : {e}"
