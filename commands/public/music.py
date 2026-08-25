"""Audio playback slash commands powered by Lavalink v4."""

import re
import asyncio
import discord
import lavalink
from discord.ext import commands
from discord import app_commands
from app.helps.utils import logger
from plugins.integrating.hosting.node_lavalink import LavalinkManager, LavalinkVoiceClient


class Music(commands.GroupCog, name="music"):
    """Music playback and queue management command group."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lavalink_manager = LavalinkManager()
        self._lavalink_ready = False
        self._connect_locks = {}

    @commands.Cog.listener()
    async def on_ready(self):
        """Initialize Lavalink connection when the bot is ready."""
        if not self._lavalink_ready:
            try:
                await asyncio.sleep(1)
                print("[INFO MUSIC] Initializing Lavalink client...")
                success = await self.lavalink_manager.connect_nodes(self.bot)
                if not success:
                    logger.warning("[WARNING MUSIC] Failed to connect to Lavalink node.")
                else:
                    if self.lavalink_manager.client and not hasattr(self.bot, "lavalink"):
                        self.bot.lavalink = self.lavalink_manager.client

                self._lavalink_ready = True
            except Exception as error:
                logger.error(f"[ERROR MUSIC] Lavalink initialization error: {error}", exc_info=True)

    async def cog_unload(self):
        """Cleanup Lavalink on cog unload."""
        await self.lavalink_manager.shutdown()

    async def _ensure_player_and_connect(self, interaction: discord.Interaction):
        """Create player and connect bot to voice channel via LavalinkVoiceClient."""
        try:
            guild = interaction.guild
            assert guild is not None
            voice_channel = interaction.user.voice.channel
            assert voice_channel is not None

            if not hasattr(self.bot, "lavalink"):
                self.bot.lavalink = self.lavalink_manager.client

            self.lavalink_manager.client.player_manager.create(guild.id)
            player = self.lavalink_manager.client.player_manager.get(guild.id)
            player.store("channel", interaction.channel.id)

            voice_client = guild.voice_client

            if voice_client:
                current_channel = voice_client.channel
                if current_channel is None or getattr(current_channel, "id", None) != voice_channel.id:
                    await voice_client.disconnect(force=True)
                    await asyncio.sleep(0.3)
                else:
                    return player

            await voice_channel.connect(cls=LavalinkVoiceClient)
            player.channel_id = str(voice_channel.id)
            return player

        except Exception as error:
            logger.error(f"[ERROR MUSIC] Error connecting to voice channel: {error}", exc_info=True)

    async def _get_guild(self, interaction: discord.Interaction) -> discord.Guild | None:
        """Validate that the interaction occurred in a guild."""
        if not interaction.guild:
            await interaction.response.send_message("Cette commande n'est disponible que dans un serveur.", ephemeral=True)
            return None
        return interaction.guild

    @app_commands.command(name="play", description="PUBLIC: Play a song or playlist in your voice channel.")
    @app_commands.describe(query="Song title or URL to stream")
    async def play(self, interaction: discord.Interaction, query: str):
        try:
            await interaction.response.defer()
            if not self.lavalink_manager.is_initialized:
                return await interaction.followup.send("Le système de musique n'est pas disponible actuellement.", ephemeral=True)

            interact_user_voice = getattr(interaction.user, "voice", None)
            if not interact_user_voice or not interact_user_voice.channel:
                return await interaction.followup.send("Vous devez être connecté dans un salon vocal pour lancer de la musique.", ephemeral=True)

            voice_channel = interact_user_voice.channel
            permissions = voice_channel.permissions_for(interaction.guild.me)

            if not permissions.connect or not permissions.speak:
                return await interaction.followup.send("Permissions insuffisantes pour rejoindre ou parler dans ce salon vocal.", ephemeral=True)

            player = await self._ensure_player_and_connect(interaction)
            await asyncio.sleep(0.5)
            if not player:
                return await interaction.followup.send("Impossible d'initialiser le lecteur audio.", ephemeral=True)

            if str(getattr(player, "channel_id", None)) != str(getattr(voice_channel, "id", None)):
                player.channel_id = str(getattr(voice_channel, "id", None))

            search = query if query.startswith(("ytsearch:", "http://", "https://")) else f"ytsearch:{query}"
            try:
                results = await player.node.get_tracks(search)
            except Exception as error:
                logger.error(f"[ERROR MUSIC] Error in get_tracks: {error}", exc_info=True)
                return await interaction.followup.send("Erreur lors de la recherche du morceau.", ephemeral=True)

            if not results or not results.tracks:
                return await interaction.followup.send(f"Aucun résultat trouvé pour `{query}`.", ephemeral=True)

            track = results.tracks[0]
            player.add(requester=interaction.user.id, track=track)

            if not player.is_playing:
                try:
                    await player.play()
                    await interaction.followup.send(f"Lecture en cours : **{track.title}** 🎵")
                except Exception as error:
                    logger.error(f"[ERROR MUSIC] Error starting playback: {error}", exc_info=True)
                    await interaction.followup.send("Erreur lors du démarrage de la lecture.", ephemeral=True)
            else:
                await interaction.followup.send(f"Ajouté à la file d'attente : **{track.title}** 📋")

        except Exception as error:
            logger.error(f"[ERROR MUSIC] Error in play command: {error}", exc_info=True)
            msg = "Une erreur s'est produite lors de la lecture."
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="stop", description="PUBLIC: Stop playback, clear queue, and disconnect.")
    async def stop(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            if not self.lavalink_manager.is_initialized:
                return await interaction.followup.send("Le système musical n'est pas disponible.", ephemeral=True)

            guild = await self._get_guild(interaction)
            if not guild:
                return

            player = await self.lavalink_manager.get_player(guild)
            if not player:
                return await interaction.followup.send("Aucune musique n'est en cours de lecture.", ephemeral=True)

            player.queue.clear()
            await player.stop()

            success = await self.lavalink_manager.disconnect_player(guild)
            if success:
                await interaction.followup.send("Musique arrêtée et déconnexion effectuée.", ephemeral=True)
            else:
                await interaction.followup.send("Musique arrêtée.", ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR MUSIC] Error in stop command: {error}", exc_info=True)
            await interaction.followup.send("Erreur lors de l'arrêt de la musique.", ephemeral=True)

    @app_commands.command(name="pause", description="PUBLIC: Pause current playback.")
    async def pause(self, interaction: discord.Interaction):
        try:
            if not self.lavalink_manager.is_initialized:
                return await interaction.response.send_message("Système musical non disponible.", ephemeral=True)

            guild = await self._get_guild(interaction)
            if not guild:
                return

            player = await self.lavalink_manager.get_player(guild)
            if not player or not player.is_playing:
                return await interaction.response.send_message("Aucune musique en cours de lecture.", ephemeral=True)

            await player.set_pause(True)
            await interaction.response.send_message("Musique mise en pause. ⏸️", ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR MUSIC] Error in pause command: {error}", exc_info=True)
            await interaction.response.send_message("Erreur lors de la mise en pause.", ephemeral=True)

    @app_commands.command(name="resume", description="PUBLIC: Resume paused playback.")
    async def resume(self, interaction: discord.Interaction):
        try:
            if not self.lavalink_manager.is_initialized:
                return await interaction.response.send_message("Système musical non disponible.", ephemeral=True)

            guild = await self._get_guild(interaction)
            if not guild:
                return

            player = await self.lavalink_manager.get_player(guild)
            if not player:
                return await interaction.response.send_message("Aucun lecteur actif.", ephemeral=True)

            if not player.paused:
                return await interaction.response.send_message("La musique n'est pas en pause.", ephemeral=True)

            await player.set_pause(False)
            await interaction.response.send_message("Reprise de la lecture. ▶️", ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR MUSIC] Error in resume command: {error}", exc_info=True)
            await interaction.response.send_message("Erreur lors de la reprise.", ephemeral=True)

    @app_commands.command(name="skip", description="PUBLIC: Skip to the next track in queue.")
    async def skip(self, interaction: discord.Interaction):
        try:
            if not self.lavalink_manager.is_initialized:
                return await interaction.response.send_message("Système musical non disponible.", ephemeral=True)

            guild = await self._get_guild(interaction)
            if not guild:
                return

            player = await self.lavalink_manager.get_player(guild)
            if not player or not player.is_playing:
                return await interaction.response.send_message("Aucune piste en cours de lecture à passer.", ephemeral=True)

            await player.skip()
            await interaction.response.send_message("Piste passée. ⏭️", ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR MUSIC] Error in skip command: {error}", exc_info=True)
            await interaction.response.send_message("Erreur lors du passage au morceau suivant.", ephemeral=True)

    @app_commands.command(name="queue", description="PUBLIC: Display upcoming tracks in queue.")
    async def queue(self, interaction: discord.Interaction):
        try:
            if not self.lavalink_manager.is_initialized:
                return await interaction.response.send_message("Système musical non disponible.", ephemeral=True)

            guild = await self._get_guild(interaction)
            if not guild:
                return

            player = await self.lavalink_manager.get_player(guild)
            if not player or not player.queue:
                return await interaction.response.send_message("La file d'attente est vide.", ephemeral=True)

            queue_list = []
            for i, track in enumerate(player.queue[:10], start=1):
                queue_list.append(f"{i}. **{track.title}**")

            queue_text = "\n".join(queue_list)
            if len(player.queue) > 10:
                queue_text += f"\n\n... et {len(player.queue) - 10} autres morceaux."

            embed = discord.Embed(
                title="File d'attente musicale",
                description=queue_text,
                color=discord.Color.blue(),
            )
            embed.set_footer(text=f"Total : {len(player.queue)} morceaux")
            await interaction.response.send_message(embed=embed, ephemeral=False)

        except Exception as error:
            logger.error(f"[ERROR MUSIC] Error in queue command: {error}", exc_info=True)
            await interaction.response.send_message("Erreur lors de l'affichage de la file d'attente.", ephemeral=True)

    @app_commands.command(name="nowplaying", description="PUBLIC: Display currently playing track.")
    async def nowplaying(self, interaction: discord.Interaction):
        try:
            if not self.lavalink_manager.is_initialized:
                return await interaction.response.send_message("Système musical non disponible.", ephemeral=True)

            guild = await self._get_guild(interaction)
            if not guild:
                return

            player = await self.lavalink_manager.get_player(guild)
            if not player or not player.current:
                return await interaction.response.send_message("Aucun morceau en cours de lecture.", ephemeral=True)

            track = player.current
            duration = lavalink.utils.format_time(track.duration)

            embed = discord.Embed(
                title="🎧 En cours de lecture",
                description=f"**[{track.title}]({track.uri})**",
                color=0xFF0921,
            )
            embed.add_field(name="Auteur", value=track.author, inline=True)
            embed.add_field(name="Durée", value=f"{duration}", inline=True)
            embed.add_field(name="Demandé par", value=f"`{interaction.user.display_name}`", inline=False)

            youtube_regex = r"(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
            research = re.search(youtube_regex, track.uri)
            if research:
                video_id = research.group(1)
                embed.set_thumbnail(url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg")

            await interaction.response.send_message(embed=embed, ephemeral=False)

        except Exception as error:
            logger.error(f"[ERROR MUSIC] Error in nowplaying command: {error}", exc_info=True)
            await interaction.response.send_message("Erreur lors de l'affichage du morceau actuel.", ephemeral=True)

    @app_commands.command(name="volume", description="PUBLIC: Adjust playback volume.")
    @app_commands.describe(level="Volume percentage (0-100)")
    async def volume(self, interaction: discord.Interaction, level: int):
        try:
            if not self.lavalink_manager.is_initialized:
                return await interaction.response.send_message("Système musical non disponible.", ephemeral=True)

            if not 0 <= level <= 100:
                return await interaction.response.send_message("Le volume doit être compris entre 0 et 100.", ephemeral=True)

            guild = await self._get_guild(interaction)
            if not guild:
                return

            player = await self.lavalink_manager.get_player(guild)
            if not player:
                return await interaction.response.send_message("Aucun lecteur actif.", ephemeral=True)

            await player.set_volume(level)
            await interaction.response.send_message(f"Volume réglé sur {level}%. 🔊", ephemeral=False)

        except Exception as error:
            logger.error(f"[ERROR MUSIC] Error in volume command: {error}", exc_info=True)
            await interaction.response.send_message("Erreur lors du réglage du volume.", ephemeral=True)

    async def _cleanup_music(self, guild: discord.Guild):
        """Cleanup music queue and disconnect from voice."""
        player = await self.lavalink_manager.get_player(guild)
        if player:
            player.queue.clear()
            await player.stop()

        if guild.voice_client:
            await guild.voice_client.disconnect(force=True)
            await asyncio.sleep(0.3)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        """Auto-disconnect bot when all human users leave the voice channel."""
        try:
            if not before.channel or after.channel:
                return

            guild = member.guild
            voice_client = guild.voice_client
            if not voice_client:
                return

            bot_user = self.bot.user
            assert bot_user is not None
            if member.id == bot_user.id:
                await self._cleanup_music(guild)
                return

            channel = before.channel
            if self.bot.user not in channel.members:
                return

            humans = [m for m in channel.members if not m.bot]
            if humans:
                return

            await self._cleanup_music(guild)

        except Exception as error:
            logger.error(f"[ERROR MUSIC] Error in on_voice_state_update: {error}", exc_info=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))