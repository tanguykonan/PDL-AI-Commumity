# ============================ COG MUSIQUE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 02/01/2026
# ==================================================================================
import re
import asyncio
import discord
import lavalink
from discord.ext import commands
from discord import app_commands
from app.helps.utils import logger
from plugins.integrating.hosting.node_lavalink import LavalinkManager, LavalinkVoiceClient


class Music(commands.GroupCog, name="music"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lavalink_manager = LavalinkManager()
        self._lavalink_ready = False
        self._connect_locks = {}

    @commands.Cog.listener()
    async def on_ready(self):
        """Initialiser Lavalink quand le bot est prêt"""
        if not self._lavalink_ready:
            try:
                await asyncio.sleep(1)
                print("[INFO MUSIC]=> Initialisation du service lavalink...")
                success = await self.lavalink_manager.connect_nodes(self.bot)
                if not success:
                    logger.warning(f'[WARNING MUSIC]-> Échec de la connexion à lavalink')
                    print(f'[WARNING MUSIC]-> Échec de la connexion à lavalink')
                else:
                    if self.lavalink_manager.client and not hasattr(self.bot, 'lavalink'):
                        self.bot.lavalink = self.lavalink_manager.client

                self._lavalink_ready = True
            except Exception as error:
                logger.error(f"[ERROR MUSIC]=> Erreur lors de l'initialisation Lavalink: {error}", exc_info=True)
                print(f"[ERROR MUSIC]=> Erreur lors de l'initialisation Lavalink: {error}")

    async  def cog_unload(self):
        """Appeler quand le cog est déchargé"""
        await self.lavalink_manager.shutdown()

    async def _ensure_player_and_connect(self, interaction: discord.Interaction):
        """Créer le player si besoin et connecte le bot au canal vocal via LavalinkVoiceClient."""
        try:
            guild = interaction.guild
            assert guild is not None
            voice_channel = interaction.user.voice.channel #type:ignore
            assert voice_channel is not None

            if not hasattr(self.bot, 'lavalink'):
                self.bot.lavalink = self.lavalink_manager.client

            self.lavalink_manager.client.player_manager.create(guild.id) #type:ignore
            player = self.lavalink_manager.client.player_manager.get(guild.id) #type:ignore
            player.store('channel', interaction.channel.id) #type:ignore

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
            logger.error(f"[ERROR MUSIC]-> Une erreur de création du player ou de connexion du bot au canal vocal via LavalinkVoiceClient s'est produite: {error}", exc_info=True)

    async def _get_guild(self, interaction: discord.Interaction) -> discord.Guild | None:
        """Retourne le guild ou envoie un message d'erreur si None"""
        _ = self
        if not interaction.guild:
            await interaction.response.send_message("Cette commande n'est disponible que dans un serveur.",ephemeral=True)
            return None
        return interaction.guild

    @app_commands.command(name="play", description="PUBLIC-> Jouer une musique")
    @app_commands.describe(query="Le nom ou l'URL de la musique à jouer")
    async def play(self, interaction: discord.Interaction, query: str):
        try:
            await interaction.response.defer()
            if not self.lavalink_manager.is_initialized:
                return await interaction.followup.send("Oh Oh, le système de musique n'est pas disponible actuellement.", ephemeral=True)

            interact_user_voice = getattr(interaction.user, "voice", None)
            if not interact_user_voice or not interact_user_voice.channel: #type:ignore
                return await interaction.followup.send("Mais putain, t'es con ou quoi ? Tu dois être dans un canal vocal pour utiliser cette commande !", ephemeral=True)

            voice_channel = interact_user_voice.channel #type:ignore
            permissions = voice_channel.permissions_for(interaction.guild.me) #type:ignore

            if not permissions.connect or not permissions.speak:
                return await interaction.followup.send("Mais pourquoi Je n'ai pas les permissions de rejoindre ou parler dans ce canal vocal !", ephemeral=True)

            player = await self._ensure_player_and_connect(interaction)
            await asyncio.sleep(0.5)
            if not player:
                return await interaction.followup.send(f"Oh merde {interaction.user.display_name} ! Tu n'as pas de chance aujourd'hui. C'est impossible de préparer un lecteur pour toi.", ephemeral=True)

            if str(getattr(player, "channel_id", None)) != str(getattr(voice_channel, "id", None)):
                player.channel_id = str(getattr(voice_channel, "id", None))

            search = query if query.startswith(("ytsearch:", "http://", "https://")) else f"ytsearch:{query}"
            try:
                results = await player.node.get_tracks(search) #type:ignore
            except Exception as error:
                logger.error(f"[ERROR MUSIC]=> Une erreur s'est produite lors du get_tracks: {error}")
                return await interaction.followup.send(f"Écoute {interaction.user.display_name}, on va faire simple. signale qu'il y a un putain de bug par ici !", ephemeral=True)

            if not results or not results.tracks:
                return await interaction.followup.send(f"Eh oh, vérifie bien que cette merde de '`{query}`' existe parce que moi je trouve pas.", ephemeral=True)

            track = results.tracks[0]
            player.add(requester=interaction.user.id, track=track) #type:ignore

            if not player.is_playing: #type:ignore
                try:
                    await player.play() #type:ignore
                    await interaction.followup.send(f"Écoutons **{track.title}** ensemble {interaction.user.display_name} !")
                except Exception as error:
                    logger.error(f"[ERROR MUSIC]-> Une erreur de démarrage d'une lecture musicale, s'est produite: {error}", exc_info=True)
                    await interaction.followup.send(f"Contact le support {interaction.user.display_name}, ça faut mieux pour nous deux.", ephemeral=True)
            else:
                await interaction.followup.send(f"Ok. J'ajoute **{track.title}** au fil en attendant.", ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR MUSIC]-> Une erreur dans la commande play s'est produite: {error}", exc_info=True)

            if interaction.response.is_done():
                return await interaction.followup.send("Mauvaise nouvelle, une erreur s'est produite lors de la lecture de cette merde.", ephemeral=True)
            else:
                return await interaction.response.send_message("Mauvaise nouvelle, une erreur s'est produite lors de la lecture de cette merde.", ephemeral=True)

    @app_commands.command(name="stop", description="PUBLIC-> Arrêter la musique")
    async def stop(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            if not self.lavalink_manager.is_initialized:
                return await interaction.followup.send("Oh Oh, le système de musique n'est pas disponible actuellement.", ephemeral=True)

            guild = await self._get_guild(interaction)
            if not guild:
                return None

            player = await self.lavalink_manager.get_player(guild)
            if not player:
                return await interaction.followup.send(f"Hum, écoute moi bien {interaction.user.display_name}, va jouer loins.", ephemeral=True)

            player.queue.clear()
            await player.stop()

            success = await self.lavalink_manager.disconnect_player(guild)
            if success:
                await interaction.followup.send("J'ai bien arrêté de jouer le lecteur de disque. Au plaisir de ne plus vous revoir.", ephemeral=True)
            else:
                await interaction.followup.send(f"Hum, écoute moi bien {interaction.user.display_name}, va jouer loins.", ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR MUSIC]-> Une erreur dans la commande stop s'est produite: {error}", exc_info=True)
            return await interaction.response.send_message("Mauvaise nouvelle, une erreur s'est produite lors de l'arrêt de cette merde.", ephemeral=True)

    @app_commands.command(name="pause", description="PUBLIC-> Mettre en pause la musique")
    async def pause(self, interaction: discord.Interaction):
        try:
            if not self.lavalink_manager.is_initialized:
                return await interaction.response.send_message("Oh Oh, le système de musique n'est pas disponible actuellement.", ephemeral=True)

            guild = await self._get_guild(interaction)
            if not guild:
                return None

            player = await self.lavalink_manager.get_player(guild)
            if not player or not player.is_playing:
                return await interaction.response.send_message(f"Je vais plutôt mettre une pause à ta vie {interaction.user.display_name} pour remplacer la musique.", ephemeral=True)

            await player.set_pause(True)
            await interaction.response.send_message(f"Bravo {interaction.user.display_name}. Cette musique est enfin en pause.", ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR MUSIC]-> Une erreur dans la commande pause, s'est produite: {error}", exc_info=True)
            return await interaction.response.send_message("Mauvaise nouvelle, une erreur s'est produite. Contact le support si le problème persiste.", ephemeral=True)

    @app_commands.command(name="resume", description="PUBLIC-> Reprendre la musique")
    async def resume(self, interaction: discord.Interaction):
        try:
            if not self.lavalink_manager.is_initialized:
                return await interaction.response.send_message(
                    "Oh Oh, le système de musique n'est pas disponible actuellement.",
                    ephemeral=True
                )

            guild = await self._get_guild(interaction)
            if not guild:
                return None

            player = await self.lavalink_manager.get_player(guild)
            if not player:
                return await interaction.response.send_message("Hum, une provocation..", ephemeral=True)

            if not player.paused:
                return await interaction.response.send_message("Met la en pause d'abord cette merde de musique !", ephemeral=True)

            await player.set_pause(False)
            await interaction.response.send_message("Je reprend ta musique.", ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR MUSIC]-> Une erreur dans la commande resume s'est produite: {error}", exc_info=True)
            return await interaction.response.send_message("Mauvaise nouvelle, une erreur s'est produite. Contact le support si le problème persiste.", ephemeral=True)

    @app_commands.command(name="skip", description="PUBLIC-> Passer à la musique suivante")
    async def skip(self, interaction: discord.Interaction):
        try:
            if not self.lavalink_manager.is_initialized:
                return await interaction.response.send_message("Oh Oh, le système de musique n'est pas disponible actuellement.", ephemeral=True)

            guild = await self._get_guild(interaction)
            if not guild:
                return None

            player = await self.lavalink_manager.get_player(guild)
            if not player or not player.is_playing:
                return await interaction.response.send_message(f"Je vais skip ta vie plutôt {interaction.user.display_name} ! Tu n'as aucune musique en cours de lecture.", ephemeral=True)

            await player.skip()
            await interaction.response.send_message(f"D'accord {interaction.user.display_name}, on saute ce disque rayé.", ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR MUSIC]-> Une erreur dans la commande skip s'est produite: {error}", exc_info=True)
            return await interaction.response.send_message("Mauvaise nouvelle, une erreur s'est produite. Contact le support si le problème persiste.", ephemeral=True)

    @app_commands.command(name="queue", description="PUBLIC-> Afficher la file d'attente")
    async def queue(self, interaction: discord.Interaction):
        try:
            if not self.lavalink_manager.is_initialized:
                return await interaction.response.send_message("Oh Oh, le système de musique n'est pas disponible actuellement.", ephemeral=True)

            guild = await self._get_guild(interaction)
            if not guild:
                return None

            player = await self.lavalink_manager.get_player(guild)
            if not player:
                return await interaction.response.send_message(f"{interaction.user.display_name}, le seule musique en attente, s'appelle *Achetez lui un cerveau*.", ephemeral=True)

            if not player.queue:
                return await interaction.response.send_message("Putain ! je ne vois rien !", ephemeral=True)

            queue_list = []
            for i, track in enumerate(player.queue[:10], start=1):  # Limite à 10
                queue_list.append(f"{i}. **{track.title}**")

            queue_text = "\n".join(queue_list)
            if len(player.queue) > 10:
                queue_text += f"\n\n... et {len(player.queue) - 10} autres morceaux."

            embed = discord.Embed(
                title="File d'attente musicale",
                description=queue_text,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Total: {len(player.queue)} morceaux")
            await interaction.response.send_message(embed=embed, ephemeral=False)

        except Exception as error:
            logger.error(f"[ERROR MUSIC]-> Une erreur dans la commande queue s'est produite: {error}", exc_info=True)
            return await interaction.response.send_message("Mauvaise nouvelle, une erreur s'est produite. Contact le support si le problème persiste.", ephemeral=True)

    @app_commands.command(name="nowplaying", description="PUBLIC-> Afficher la musique en cours")
    async def nowplaying(self, interaction: discord.Interaction):
        try:
            if not self.lavalink_manager.is_initialized:
                return await interaction.response.send_message("Oh Oh, le système de musique n'est pas disponible actuellement.", ephemeral=True)

            guild = await self._get_guild(interaction)
            if not guild:
                return None

            player = await self.lavalink_manager.get_player(guild)
            if not player or not player.current:
                return await interaction.response.send_message("Tu n'écoute rien putain !", ephemeral=True)

            track = player.current
            """position = lavalink.utils.format_time(player.position)"""
            duration = lavalink.utils.format_time(track.duration)

            embed = discord.Embed(
                title="🎧 En cours de lecture",
                description=f"**[{track.title}]({track.uri})**",
                color=0xFF0921
            )
            embed.add_field(name="**Auteur**", value=track.author, inline=True)
            embed.add_field(name="**Durée**", value=f"{duration}", inline=True)
            embed.add_field(name="**Démandé par**", value=f"`{interaction.user.display_name}`", inline=False)

            youtube_regex = (
                r"(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)"
                r"([a-zA-Z0-9_-]{11})"
            )
            research = re.search(youtube_regex, track.uri)
            if research:
                video_id = research.group(1)
                embed.set_thumbnail(
                    url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                )
            """
            thumbnail = getattr(track, 'thumbnail', None)
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            """
            await interaction.response.send_message(embed=embed, ephemeral=False)

        except Exception as error:
            logger.error(f"[ERROR MUSIC]-> Une erreur dans la commande nowplaying s'est produite: {error}", exc_info=True)
            return await interaction.response.send_message("Mauvaise nouvelle, une erreur s'est produite. Contact le support si le problème persiste.", ephemeral=True)

    @app_commands.command(name="volume", description="PUBLIC-> Ajuster le volume")
    @app_commands.describe(level="Niveau de volume (0-100)")
    async def volume(self, interaction: discord.Interaction, level: int):
        try:
            if not self.lavalink_manager.is_initialized:
                return await interaction.response.send_message("Oh Oh, le système de musique n'est pas disponible actuellement.", ephemeral=True)

            if not 0 <= level <= 100:
                return await interaction.response.send_message(f"{interaction.user.display_name}, rassure moi. Un volume tu sais que c'est toujours entre 0 et 100 !?", ephemeral=False)

            guild = await self._get_guild(interaction)
            if not guild:
                return None

            player = await self.lavalink_manager.get_player(guild)
            if not player:
                return await interaction.response.send_message("Je préfère de répondre en cachette parce que là, tu as fait fort.", ephemeral=True)

            await player.set_volume(level)
            await interaction.response.send_message(f"Je met le volume {level}% pour cette putain de scéance musicale.", ephemeral=False)

        except Exception as error:
            logger.error(f"[ERROR MUSIC]-> Une erreur dans la commande volume s'est produite: {error}", exc_info=True)
            return await interaction.response.send_message("Mauvaise nouvelle, une erreur s'est produite. Contact le support si le problème persiste.", ephemeral=True)

    # ÉVÉNEMENTS
    async def _cleanup_music(self, guild: discord.Guild):
        player = await self.lavalink_manager.get_player(guild)
        if player:
            player.queue.clear()
            await player.stop()

        if guild.voice_client:
            await guild.voice_client.disconnect(force=True) #type:ignore
            await asyncio.sleep(0.3)

    @commands.Cog.listener()
    async def on_voice_state_update(
            self,
            member: discord.Member,
            before: discord.VoiceState,
            after: discord.VoiceState
    ):
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
            logger.error(f"[ERROR MUSIC]=> Une erreur lors des changements d'état vocal s'est produite: {error}", exc_info=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))