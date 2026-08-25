"""Server moderation, punishment, and configuration slash commands for guild administrators."""

import re
import datetime
from typing import Optional
import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from app.helps.utils import logger
from app.helps.config_ui import build_accueil_embed_page, AccueilView


class Staff(commands.GroupCog, name="staff"):
    """Guild moderation and administration command group."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    async def _check_guild_context(interaction: discord.Interaction) -> bool:
        """Validate that the command was executed in a guild."""
        if interaction.guild is None:
            return False
        return True

    @staticmethod
    def _parse_time(time_str: str) -> Optional[datetime.timedelta]:
        """Convert duration string (e.g. '1d', '2h', '30m', '60s') into a timedelta."""
        try:
            if not time_str:
                return None

            pattern = r"^(\d+)([dhms])$"
            match = re.match(pattern, time_str.lower().strip())
            if not match:
                return None

            amount_str, unit = match.groups()
            amount = int(amount_str)

            if unit == "d" and amount > 365:
                return None
            if unit == "h" and amount > 8760:
                return None
            if unit == "m" and amount > 525600:
                return None
            if unit == "s" and amount > 31536000:
                return None

            if unit == "d":
                return datetime.timedelta(days=amount)
            if unit == "h":
                return datetime.timedelta(hours=amount)
            if unit == "m":
                return datetime.timedelta(minutes=amount)
            if unit == "s":
                return datetime.timedelta(seconds=amount)

            return None
        except Exception as error:
            logger.error(f"[ERROR STAFF] Error parsing duration: {error}", exc_info=True)
            return None

    @staticmethod
    def _format_time(time_str: str) -> str:
        """Format duration string into a readable representation."""
        try:
            if not time_str:
                return "indéterminée"

            pattern = r"^(\d+)([dhms])$"
            match = re.match(pattern, time_str.lower().strip())
            if not match:
                return time_str

            amount, unit = match.groups()
            units = {
                "d": "jour(s)",
                "h": "heure(s)",
                "m": "minute(s)",
                "s": "seconde(s)",
            }
            return f"{amount} {units.get(unit, unit)}"
        except Exception as error:
            logger.error(f"[ERROR STAFF] Error formatting duration: {error}", exc_info=True)
            return "indéterminée"

    @staticmethod
    async def _check_member_hierarchy(
        interaction: discord.Interaction,
        target: discord.Member,
    ) -> tuple[bool, str | None]:
        """Verify role hierarchy between moderator, target, and the bot."""
        try:
            if not isinstance(target, discord.Member):
                return False, "L'utilisateur n'est pas membre de ce serveur."

            if target.id == interaction.user.id:
                return False, "Vous ne pouvez pas vous sanctionner vous-même."

            if target.id == getattr(interaction.guild, "owner_id"):
                return False, "Impossible de sanctionner le propriétaire du serveur."

            if interaction.client.user and target.id == getattr(interaction.client.user, "id"):
                return False, "Impossible de sanctionner le bot."

            if isinstance(interaction.user, discord.Member):
                if (
                    target.top_role >= interaction.user.top_role
                    and interaction.user.id != getattr(interaction.guild, "owner_id")
                ):
                    return False, "Vous ne pouvez pas sanctionner un membre avec un rôle supérieur ou égal au vôtre."

            bot_member = getattr(interaction.guild, "me")
            if bot_member is None:
                return False, "Impossible de vérifier la hiérarchie du bot."

            if target.top_role >= bot_member.top_role:
                return False, "Le rôle de l'utilisateur est supérieur ou égal à celui du bot."

            return True, None
        except Exception as error:
            logger.error(f"[ERROR STAFF] Hierarchy check error: {error}", exc_info=True)
            return False, "Une erreur s'est produite lors de la vérification de la hiérarchie."

    @app_commands.command(name="config", description="Open interactive guild configuration panel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def config(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            if interaction.guild is None:
                return await interaction.followup.send("Cette commande doit être exécutée dans un serveur.")

            embed = build_accueil_embed_page(interaction)
            view = AccueilView(interaction, interaction.guild.id)
            message = await interaction.followup.send(embed=embed, view=view)
            view.message = message

        except Exception as error:
            logger.error(f"[ERROR STAFF] Error opening config panel: {error}", exc_info=True)
            await interaction.followup.send("Une erreur est survenue lors de l'ouverture du panneau de configuration.", ephemeral=True)

    @app_commands.command(name="punish", description="PUBLIC: Apply a timeout, kick, or ban sanction.")
    @app_commands.describe(
        penalty="Sanction type to apply",
        user="Target member",
        time="Duration (e.g. 1d, 2h, 30m, 60s)",
        reason="Reason for sanction",
    )
    @app_commands.choices(
        penalty=[
            Choice(name="mute", value="mute"),
            Choice(name="kick", value="kick"),
            Choice(name="ban", value="ban"),
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def punish(
        self,
        interaction: discord.Interaction,
        penalty: Choice[str],
        user: discord.Member,
        time: Optional[str] = None,
        reason: Optional[str] = "Aucune raison fournie",
    ):
        try:
            await interaction.response.defer()

            if not await self._check_guild_context(interaction):
                return await interaction.followup.send("Cette commande doit être exécutée dans un serveur.", ephemeral=True)

            can_punish, error_msg = await self._check_member_hierarchy(interaction, user)
            if not can_punish:
                return await interaction.followup.send(error_msg, ephemeral=True)

            guild = interaction.guild
            if guild is None:
                return await interaction.followup.send("Erreur de contexte de serveur.", ephemeral=True)

            bot_member = guild.me
            if bot_member is None:
                return await interaction.followup.send("Erreur de permissions du bot.", ephemeral=True)

            if penalty.value == "mute":
                if not bot_member.guild_permissions.moderate_members:
                    return await interaction.followup.send("Le bot n'a pas la permission d'exclure temporairement des membres.", ephemeral=True)

                if not time:
                    return await interaction.followup.send("Veuillez spécifier une durée (ex: `1d`, `2h`, `30m`).", ephemeral=True)

                duration = self._parse_time(time)
                if not duration:
                    return await interaction.followup.send("Format de durée invalide. Utilisez : `1d`, `2h`, `30m`, `60s`.", ephemeral=True)

                max_timeout = datetime.timedelta(days=28)
                if duration > max_timeout:
                    return await interaction.followup.send("La durée maximale pour un timeout est de 28 jours.", ephemeral=True)

                until = user.timed_out_until
                if user.is_timed_out() and until:
                    return await interaction.followup.send(f"{user.mention} est déjà mute jusqu'à <t:{int(until.timestamp())}:R>.", ephemeral=True)

                await user.timeout(duration, reason=f"{reason} | Par: {interaction.user.display_name}")

                formatted_time = self._format_time(time)
                until_timestamp = int((discord.utils.utcnow() + duration).timestamp())

                await interaction.followup.send(
                    f"{user.mention} a été rendu muet jusqu'au : <t:{until_timestamp}:F> (<t:{until_timestamp}:R>)",
                    ephemeral=False,
                )

                try:
                    await user.send(
                        f"Vous avez été rendu muet sur **{guild.name}** pour une durée de **{formatted_time}**\n📝 **Raison**: {reason}"
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass

            elif penalty.value == "kick":
                if not bot_member.guild_permissions.kick_members:
                    return await interaction.followup.send("Le bot n'a pas la permission d'expulser des membres.", ephemeral=True)

                try:
                    await user.send(f"Vous avez été expulsé de **{guild.name}** pour la raison suivante : {reason}")
                except (discord.Forbidden, discord.HTTPException):
                    pass

                await guild.kick(user, reason=f"{reason} | Par: {interaction.user.display_name}")
                await interaction.followup.send(f"{user.display_name} a été expulsé du serveur.", ephemeral=False)

            elif penalty.value == "ban":
                if not bot_member.guild_permissions.ban_members:
                    return await interaction.followup.send("Le bot n'a pas la permission de bannir des membres.", ephemeral=True)

                try:
                    await guild.fetch_ban(user)
                    return await interaction.followup.send(f"{user.display_name} est déjà banni.", ephemeral=True)
                except discord.NotFound:
                    pass

                try:
                    await user.send(f"Vous avez été banni de **{guild.name}** pour la raison suivante : {reason}")
                except (discord.Forbidden, discord.HTTPException):
                    pass

                await guild.ban(user, reason=f"{reason} | Par: {interaction.user.display_name}", delete_message_seconds=604800)
                await interaction.followup.send(f"{user.display_name} a été banni du serveur.", ephemeral=False)

        except Exception as error:
            logger.error(f"[ERROR STAFF] Error punishing user {user}: {error}", exc_info=True)
            return await interaction.followup.send("Une erreur s'est produite lors de l'application de la sanction.", ephemeral=True)

    @app_commands.command(name="contest", description="PUBLIC: Revoke a member timeout or ban.")
    @app_commands.describe(penalty="Sanction to revoke", user="Target user")
    @app_commands.choices(
        penalty=[
            Choice(name="unmute", value="unmute"),
            Choice(name="unban", value="unban"),
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def contest(
        self,
        interaction: discord.Interaction,
        penalty: Choice[str],
        user: discord.User,
    ):
        try:
            await interaction.response.defer()

            if not await self._check_guild_context(interaction):
                return await interaction.followup.send("Cette commande doit être exécutée dans un serveur.", ephemeral=True)

            guild = interaction.guild
            assert guild is not None

            if penalty.value == "unmute":
                if not guild.me.guild_permissions.moderate_members:
                    return await interaction.followup.send("Le bot n'a pas la permission de gérer les exclusions temporaires.", ephemeral=True)

                try:
                    member = await guild.fetch_member(user.id)
                except discord.NotFound:
                    return await interaction.followup.send(f"{user.mention} n'est pas membre de ce serveur.", ephemeral=True)
                except discord.HTTPException:
                    return await interaction.followup.send("Impossible de récupérer les informations du membre.", ephemeral=True)

                can_unmute, error_msg = await self._check_member_hierarchy(interaction, member)
                if not can_unmute:
                    return await interaction.followup.send(error_msg, ephemeral=True)

                if not member.is_timed_out():
                    return await interaction.followup.send(f"{member.mention} n'est pas actuellement muet.", ephemeral=True)

                await member.timeout(None, reason=f"Unmute par: {interaction.user.display_name}")
                await interaction.followup.send(f"{member.mention} a été dé-mute.", ephemeral=True)

                try:
                    await member.send(f"Votre sanction a été levée sur **{guild.name}**.")
                except (discord.Forbidden, discord.HTTPException):
                    pass

            elif penalty.value == "unban":
                if not guild.me.guild_permissions.ban_members:
                    return await interaction.followup.send("Le bot n'a pas la permission de gérer les bannissements.", ephemeral=True)

                try:
                    await guild.fetch_ban(user)
                except discord.NotFound:
                    return await interaction.followup.send(f"{user.mention} n'est pas banni de ce serveur.", ephemeral=True)
                except discord.HTTPException:
                    return await interaction.followup.send("Impossible de vérifier le statut de bannissement.", ephemeral=True)

                await guild.unban(user, reason=f"Unban par: {interaction.user.display_name}")
                await interaction.followup.send(f"{user.mention} a été débanni.", ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR STAFF] Error revoking sanction for {user}: {error}", exc_info=True)
            return await interaction.followup.send("Une erreur s'est produite lors de la révocation de la sanction.", ephemeral=True)

    @app_commands.command(name="clear", description="Bulk delete recent messages in the current channel.")
    @app_commands.describe(number="Number of messages to delete (1-100, default 5)")
    @app_commands.checks.has_permissions(administrator=True)
    async def clear(self, interaction: discord.Interaction, number: int = 5):
        try:
            await interaction.response.defer()
            if interaction.channel is None or not isinstance(interaction.channel, discord.TextChannel):
                return await interaction.followup.send("Cette commande doit être exécutée dans un salon textuel.")

            if number < 1:
                return await interaction.followup.send("Vous devez supprimer au moins 1 message.", ephemeral=True)
            if number > 100:
                return await interaction.followup.send("Impossible de supprimer plus de 100 messages à la fois.", ephemeral=True)

            deleted = [msg for msg in await interaction.channel.purge(limit=number) if msg is not None]
            await interaction.followup.send(f"🧹 **{len(deleted)}** message(s) supprimé(s).", ephemeral=True)
        except discord.Forbidden:
            return await interaction.followup.send("Permissions insuffisantes pour supprimer des messages.", ephemeral=True)
        except Exception as error:
            logger.error(f"[ERROR STAFF] Error clearing messages: {error}", exc_info=True)
            return await interaction.followup.send("Une erreur s'est produite lors de la suppression des messages.", ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle permission errors for staff commands."""
        if isinstance(error, app_commands.errors.MissingPermissions):
            if interaction.response.is_done():
                await interaction.followup.send("Vous n'avez pas les permissions nécessaires pour exécuter cette commande.", ephemeral=True)
            else:
                await interaction.response.send_message("Vous n'avez pas les permissions nécessaires pour exécuter cette commande.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Staff(bot))