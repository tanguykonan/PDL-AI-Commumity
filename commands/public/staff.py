# ============================ COG MUSIQUE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 02/01/2026
# ==================================================================================
import re
import discord
import datetime
from typing import Optional
from discord.ext import commands
from discord import app_commands
from app.helps.utils import logger
from discord.app_commands import Choice
from app.helps.config_ui import build_accueil_embed_page, AccueilView

class Staff(commands.GroupCog, name = 'staff'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    async def _check_guild_context(interaction: discord.Interaction) -> bool:
        """Vérifier que les commandes sont bien exécutées dans un serveur"""
        if interaction.guild is None:
            return False
        return True

    @staticmethod
    def _parse_time(time_str: str) -> Optional[datetime.timedelta]:
        """Convertit une chaîne comme '1d', '2h', '30m' en timedelta"""
        try:
            if not time_str:
                return None

            pattern = r'^(\d+)([dhms])$'
            match = re.match(pattern, time_str.lower().strip())
            if not match:
                return None

            amount_str, unit = match.groups()
            amount = int(amount_str)

            if unit == 'd' and amount > 365:
                return None
            if unit == 'h' and amount > 8760:
                return None
            if unit == 'm' and amount > 525600:
                return None
            if unit == 's' and amount > 31536000:
                return None

            if unit == 'd':
                return datetime.timedelta(days=amount)
            if unit == 'h':
                return datetime.timedelta(hours=amount)
            if unit == 'm':
                return datetime.timedelta(minutes=amount)
            if unit == 's':
                return datetime.timedelta(seconds=amount)

            return None
        except Exception as error:
            logger.error(error, exc_info=True)
            return None

    @staticmethod
    def _format_time(time_str: str) -> str:
        """Formate joliment le temps"""
        try:
            if not time_str:
                return "indéterminée"

            pattern = r'^(\d+)([dhms])$'
            match = re.match(pattern, time_str.lower().strip())
            if not match:
                return time_str

            amount, unit = match.groups()

            units = {
                'd': 'jour(s)',
                'h': 'heure(s)',
                'm': 'minute(s)',
                's': 'seconde(s)',
            }

            return f"{amount} {units.get(unit, unit)}"
        except Exception as error:
            logger.error(error, exc_info=True)
            return "indéterminée"

    @staticmethod
    async def _check_member_hierarchy(
            interaction: discord.Interaction,
            target: discord.Member
    ) -> tuple[bool, str | None]:
        """Vérifie la hiérarchie des membres"""
        try:
            if not isinstance(target, discord.Member):
                return False, "L'utilisateur n'est pas membre de ce serveur."

            if target.id == interaction.user.id:
                return False, "Tu ne peux pas te sanctionner toi-même !"

            if target.id == getattr(interaction.guild, "owner_id"):
                return False, "Tu ne peux pas sanctionner le propriétaire du serveur !"

            if interaction.client.user and target.id == getattr(interaction.client.user, "id"):
                return False, "Pourquoi tu veux me sanctionner ?"

            if isinstance(interaction.user, discord.Member):
                if (
                        target.top_role >= interaction.user.top_role
                        and interaction.user.id != getattr(interaction.guild, "owner_id")
                ):
                    return False, (
                        "Tu ne peux pas sanctionner quelqu'un avec un rôle égal ou supérieur au tien."
                    )

            bot_member = getattr(interaction.guild, "me")
            if bot_member is None:
                return False, "Impossible de vérifier ma hiérarchie."

            if target.top_role >= bot_member.top_role:
                return False, (
                    "Je ne peux pas sanctionner quelqu'un avec un rôle égal ou supérieur au mien."
                )

            return True, None
        except Exception as error:
            logger.error(error, exc_info=True)
            return False, "Une erreur s'est produite lors de la vérification."

    # ================================================================================================#
    # ============================== SYSTÈME DE CONFIGURATION ========================================#
    # ================================================================================================#
    @app_commands.command(name="config", description="Configurer le bot pour le serveur")
    @app_commands.checks.has_permissions(administrator=True)
    async def config(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            if interaction.guild is None:
                return await interaction.followup.send("Hé, Cette commande doit être exécutée dans un serveur (dans lequel tu es au minimum administrateur/trice).")

            embed = build_accueil_embed_page(interaction)
            view = AccueilView(interaction, interaction.guild.id) #type:ignore
            message = await interaction.followup.send(embed=embed, view=view)
            view.message = message

        except Exception as error:
            logger.error(f"[ERROR STAFF]-> Une erreur s'est produite durant le processus d'affichage du panel de configuration: {error}", exc_info=True)
            await interaction.followup.send("Une erreur est survenue. Merci de contacter le support via (/help support) si le problème persiste.", ephemeral=True)

    # ================================================================================================#
    # ============================= COMMANDES DE MODÉRATION MANUEL ===================================#
    # ================================================================================================#
    @app_commands.command(name='punish', description='PUBLIC-> Sanctionner un membre du serveur')
    @app_commands.describe(
        penalty="Sélectionnez le type de sanction à appliquer",
        user="Utilisateur",
        time='Durée (format: 1d=jours, 2h=heures, 30m=minutes, 60s=secondes)',
        reason="Raison de la sanction"
    )
    @app_commands.choices(penalty=[
        Choice(name='mute', value='mute'),
        Choice(name='kick', value='kick'),
        Choice(name='ban', value='ban'),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def punish(
            self,
            interaction: discord.Interaction,
            penalty: Choice[str],
            user: discord.Member,
            time: Optional[str] = None,
            reason: Optional[str] = "Aucune raison fournie"
    ):
        try:
            await interaction.response.defer()

            if not await self._check_guild_context(interaction):
                return await interaction.followup.send(f'S\'il te plait {interaction.user.display_name} 🙈 rejoins un serveur avant d\'exécuter cette commande.', ephemeral=True)

            can_punish, error_msg = await self._check_member_hierarchy(interaction, user)
            if not can_punish:
                return await interaction.followup.send(error_msg, ephemeral=True)

            guild = interaction.guild
            if guild is None:
                return await interaction.followup.send("Mauvaise nouvelle, une erreur s'est produite. Contact le support si le problème persiste.", ephemeral=True)

            bot_member = guild.me
            if bot_member is None:
                return await interaction.followup.send("Mauvaise nouvelle, une erreur s'est produite. Contact le support si le problème persiste.", ephemeral=True)

            if penalty.value == 'mute':

                if not bot_member.guild_permissions.moderate_members:
                    return await interaction.followup.send("Hey ! Je n'ai pas la permission d'exclure temporairement des membres.", ephemeral=True)

                if not time:
                    return await interaction.followup.send("Hé Oh, tu dois spécifier une durée pour le mute.\nExemples: `1d` (1 jour), `2h` (2 heures), `30m` (30 minutes).", ephemeral=True)

                duration = self._parse_time(time)
                if not duration:
                    return await interaction.followup.send("Bon écoute. La durée a un format invalide.\nUtilise: `1d` (jours), `2h` (heures), `30m` (minutes), `60s` (secondes)", ephemeral=True)

                max_timeout = datetime.timedelta(days=28)
                if duration > max_timeout:
                    return await interaction.followup.send(f"La durée maximale pour un timeout est de 28 jours, {interaction.user.display_name} ..", ephemeral=True)

                until = user.timed_out_until
                if user.is_timed_out() and until:
                    return await interaction.followup.send(f"Même en étant mute, on veut toujours le mute. Désolé mais {user.mention} est déjà mute jusqu'à <t:{int(until.timestamp())}:R>.", ephemeral=True)

                await user.timeout(
                    duration,
                    reason=f"{reason} | Par: {interaction.user.display_name}"
                )

                formatted_time = self._format_time(time)
                until_timestamp = int((discord.utils.utcnow() + duration).timestamp())

                await interaction.followup.send(
                    f"{user.mention} est mute jusqu'au: <t:{until_timestamp}:F> (<t:{until_timestamp}:R>)\n"
                    "https://tenor.com/view/mute-real-housewives-of-atlanta-muted-shh-quiet-gif-17545855",
                    ephemeral=False
                )

                try:
                    await user.send(
                        f"Tu as été mute sur **{guild.name}** pour une durée de **{formatted_time}**\n"
                        f"📝 **Raison**: {reason}\n"
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass

            elif penalty.value == 'kick':

                if not bot_member.guild_permissions.kick_members:
                    return await interaction.followup.send("Hey ! Je n'ai pas la permission d'expulser des membres.", ephemeral=True)

                try:
                    await user.send(
                        f"Tu as été expulsé de **{guild.name}** pour la raison suivante: {reason}\n"
                        f"Tu peux toujours revenir à nouveau avec une nouvelle invitation."
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass

                await guild.kick(user, reason=f"{reason} | Par: {interaction.user}")
                await interaction.followup.send(
                    f"{user.display_name} a été expulsé\n"
                    f"https://tenor.com/view/garfield-fight-fighting-fight-club-kitty-gif-16493778",
                    ephemeral=False
                )

            elif penalty.value == 'ban':

                if not bot_member.guild_permissions.ban_members:
                    return await interaction.followup.send("Hey ! Je n'ai pas la permission de bannir des membres.", ephemeral=True)

                try:
                    await guild.fetch_ban(user)
                    return await interaction.followup.send(f"Même en étant banni, {user.display_name} continue de faire des ravages.", ephemeral=True)
                except discord.NotFound:
                    pass

                try:
                    ban_message = f"Tu as été banni de **{guild.name}** pour la raison suivante: {reason}"
                    await user.send(ban_message)
                except (discord.Forbidden, discord.HTTPException):
                    pass

                await guild.ban(
                    user,
                    reason=f"{reason} | Par: {interaction.user}",
                    delete_message_seconds=604800 # 7 jours
                )

                await interaction.followup.send(
                    f"{user.display_name}\n"
                    f"https://tenor.com/view/banned-admin-hulk-gif-18033317",
                    ephemeral=False
                )

        except Exception as error:
            logger.error(f'[ERROR STAFF]=> Une erreur s\'est produite lors de l\'application d\'une sanction à {user} par {interaction.user.display_name}: {error}', exc_info=True)
            return await interaction.followup.send("Mauvaise nouvelle, une erreur s'est produite. Contact le support si le problème persiste.", ephemeral=True)

    @app_commands.command(name='contest', description='PUBLIC-> Supprimer les sanctions d\'un membre du serveur')
    @app_commands.describe(
        penalty="Quelle était la sanction ?",
        user="Utilisateur visé"
    )
    @app_commands.choices(penalty=[
        Choice(name='unmute', value='unmute'),
        Choice(name='unban', value='unban'),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def contest(
            self,
            interaction: discord.Interaction,
            penalty: Choice[str],
            user: discord.User
    ):
        try:
            await interaction.response.defer()

            if not await self._check_guild_context(interaction):
                return await interaction.followup.send(f'S\'il te plaît {interaction.user.display_name} rejoins un serveur avant d\'executer cette commande.', ephemeral=True)

            guild = interaction.guild
            assert guild is not None
            if penalty.value == 'unmute':

                if not guild.me.guild_permissions.moderate_members:
                    return await interaction.followup.send("Hey ! Je n'ai pas la permission d'exclure temporairement des membres.", ephemeral=True)

                try:
                    member = await guild.fetch_member(user.id) #type:ignore
                except discord.NotFound:
                    return await interaction.followup.send(f"{user.mention} n'est pas ou n'est plus membre du serveur.", ephemeral=True)
                except discord.HTTPException:
                    return await interaction.followup.send("Hey ! Impossible de récupérer les informations du membre.", ephemeral=True)

                can_unmute, error_msg = await self._check_member_hierarchy(interaction, member)
                if not can_unmute:
                    return await interaction.followup.send(error_msg, ephemeral=True)

                if not member.is_timed_out():
                    return await interaction.followup.send(f"{member.mention} n'est pas actuellement mute. Donc, on le fait d'abord.", ephemeral=True)

                await member.timeout(None, reason=f"Unmute par: {interaction.user.display_name}")
                await interaction.followup.send(f"{member.mention} peut à nouveau parler.", ephemeral=True)

                try:
                    await member.send(f"Ton mute a été levé sur **{guild.name}**")
                except (discord.Forbidden, discord.HTTPException):
                    pass

            elif penalty.value == 'unban':

                if not guild.me.guild_permissions.ban_members:
                    return await interaction.followup.send("Hey ! Je n'ai pas la permission de gérer des bans.", ephemeral=True)

                try:
                    await guild.fetch_ban(user)
                except discord.NotFound:
                    return await interaction.followup.send(f"{user.mention} n'est pas banni de ce serveur. Donc si tu veux, on va d'abord le faire.", ephemeral=True)
                except discord.HTTPException:
                    return await interaction.followup.send("Malheureusement, impossible de vérifier le statut de ban.", ephemeral=True)

                await guild.unban(user, reason=f"Unban par: {interaction.user.display_name}")
                await interaction.followup.send(f"{user.mention} a été dé-banni.", ephemeral=True)

                try:
                    await user.send(f"Tu as été dé-banni de **{guild.name}**. Tu peux maintenant rejoindre avec une invitation.")
                except (discord.Forbidden, discord.HTTPException):
                    pass

        except Exception as error:
            logger.error(f'[ERROR STAFF]-> Une erreur s\'est produite lors de la suppression d\'une sanction de {user} par {interaction.user.display_name}: {error}', exc_info=True)
            return await interaction.followup.send("Mauvaise nouvelle, une erreur s'est produite. Contact le support si le problème persiste.", ephemeral=True)

    @app_commands.command(name='clear', description='Supprimer des message sur le serveur')
    @app_commands.describe(number='Le nombre de message à supprimer (5 par défaut)')
    @app_commands.checks.has_permissions(administrator=True)
    async def clear(self, interaction: discord.Interaction, number: int = 5):
        try:
            await interaction.response.defer()
            if interaction.channel is None or not isinstance(interaction.channel, discord.TextChannel):
                return await interaction.followup.send("Mais putain ! Cette commande doit être utilisée dans un salon textuel.", ephemeral=False)

            if number < 1:
                return await interaction.followup.send(f"{interaction.user.display_name} ;-; Tu dois supprimer au moins **1 message** bon sent.", ephemeral=True)
            elif number > 100:
                return await interaction.followup.send(f"Écoute {interaction.user.display_name}. Le mieux, c'est de supprimer ce salon parce que **100 messages** d'un coup, c'est **non**.", ephemeral=True)
            else:
                deleted = [msg for msg in await interaction.channel.purge(limit=number) if msg is not None]
                await interaction.followup.send(f"<:peepobusinesstux:1464441409397330115> **{len(deleted)}** merde(s) supprimé(s) d'un coup. Chapeau !", ephemeral=True)
        except discord.Forbidden:
            return await interaction.followup.send(f"{interaction.user.display_name}, je n'ai pas la permission de supprimer des messages. C'est frustrant ;-;", ephemeral=True)
        except Exception as error:
            logger.error(f"[ERROR STAFF]=> Une erreur s'est produite lors de la suppression de message par {interaction.user.display_name}: {error}", exc_info=True)
            return await interaction.followup.send("Mauvaise nouvelle, une erreur s'est produite. Contact le support si le problème persiste.", ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            _ = self
            if interaction.response.is_done():
                await interaction.followup.send("Mais putain, tu fou quoi toi ? T'en as pas le droit tu m'entends !?", ephemeral=True)
            else:
                await interaction.response.send_message("Mais putain, tu fou quoi toi ? T'en as pas le droit tu m'entends !?", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Staff(bot))