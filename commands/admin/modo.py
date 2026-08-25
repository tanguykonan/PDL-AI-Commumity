"""Moderation and administration slash commands for managing bot admins, blacklists, and statuses."""

from typing import Optional
import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from app.helps.utils import UsefulMethods, logger
from plugins.integrating.storing.database import database


class Modo(commands.GroupCog, name="modo"):
    """Global bot moderation command group."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="define", description="ADMIN: Add a value to a database configuration list.")
    @app_commands.describe(
        key="The target configuration list",
        user="Target user",
        server="Target guild ID",
        status="Custom status text",
    )
    @app_commands.choices(
        key=[
            Choice(name="Bot admins", value="adminList"),
            Choice(name="Bot status", value="botStatusList"),
            Choice(name="Ban user", value="userBlackList"),
            Choice(name="Ban server", value="serverBlackList"),
        ]
    )
    async def define(
        self,
        interaction: discord.Interaction,
        key: Choice[str],
        user: Optional[discord.User] = None,
        server: Optional[str] = None,
        status: Optional[str] = None,
    ):
        try:
            if not await UsefulMethods.check_is_guild(interaction):
                return await interaction.response.send_message("Commande indisponible en messages privés.", ephemeral=True)

            member = interaction.user
            assert member is not None
            has_permissions = database.is_admin(member.id) or UsefulMethods.check_is_support_member(member.id)

            if not has_permissions:
                logger.warning(f"[WARNING MODO] Unauthorized access attempt by user {member.id}")
                return await interaction.response.send_message("Accès refusé. Vous n'avez pas les permissions nécessaires.", ephemeral=True)

            if key.value == "adminList":
                if user is None:
                    return await interaction.response.send_message("Veuillez spécifier un utilisateur.", ephemeral=True)
                if user.bot:
                    return await interaction.response.send_message("Impossible d'ajouter un bot comme administrateur.", ephemeral=True)

                if database.is_admin(user.id):
                    return await interaction.response.send_message(f"{user.mention} est déjà un administrateur.", ephemeral=True)
                database.add_admin(user.id)
                return await interaction.response.send_message(f"{user.mention} a été ajouté aux administrateurs du bot.", ephemeral=True)

            elif key.value == "userBlackList":
                if user is None:
                    return await interaction.response.send_message("Veuillez spécifier un utilisateur.", ephemeral=True)
                if database.is_admin(user.id):
                    return await interaction.response.send_message("Impossible de bannir un administrateur du bot.", ephemeral=True)

                if database.is_user_banned(user.id):
                    return await interaction.response.send_message(f"{user.mention} est déjà banni.", ephemeral=True)
                database.ban_user(user.id)
                return await interaction.response.send_message(f"{user.mention} a été ajouté à la liste noire.", ephemeral=True)

            elif key.value == "serverBlackList":
                if server is None:
                    return await interaction.response.send_message("Veuillez spécifier l'identifiant du serveur.", ephemeral=True)
                if not server.isdigit():
                    return await interaction.response.send_message(f"L'identifiant `{server}` n'est pas valide.", ephemeral=True)

                guild_id = int(server)
                guild = interaction.guild
                assert guild is not None
                if guild_id == guild.id:
                    return await interaction.response.send_message("Impossible de bannir le serveur actuel depuis celui-ci.", ephemeral=True)

                target_guild = self.bot.get_guild(guild_id)
                guild_name = target_guild.name if target_guild is not None else f"{guild_id}"

                if database.is_server_banned(guild_id):
                    return await interaction.response.send_message(f"Le serveur `{guild_name}` est déjà banni.", ephemeral=True)
                database.ban_server(guild_id)
                return await interaction.response.send_message(f"Le serveur `{guild_name}` a été banni.", ephemeral=True)

            elif key.value == "botStatusList":
                if status is None or not status.strip():
                    return await interaction.response.send_message("Veuillez fournir un texte de statut.", ephemeral=True)

                status_text = status.strip()
                if len(status_text) > 128:
                    return await interaction.response.send_message("Le statut ne doit pas dépasser 128 caractères.", ephemeral=True)

                if status_text in database.get_activities():
                    return await interaction.response.send_message(f"Le statut `{status_text}` existe déjà.", ephemeral=True)
                database.add_activity(status_text)
                return await interaction.response.send_message(f"Le statut `{status_text}` a été ajouté avec succès.", ephemeral=True)

        except ValueError as error:
            logger.error(f"[ERROR MODO] Validation error for key '{key.value}': {error}", exc_info=True)
            return await interaction.response.send_message("Valeur fournie invalide.", ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR MODO] Error defining value: {error}", exc_info=True)
            return await interaction.response.send_message("Une erreur s'est produite lors de l'exécution de la commande.", ephemeral=True)

    @app_commands.command(name="remove", description="ADMIN: Remove a value from a database configuration list.")
    @app_commands.describe(
        key="The target configuration list",
        user="Target user",
        server="Target guild ID",
        status="Custom status text",
    )
    @app_commands.choices(
        key=[
            Choice(name="Bot admins", value="adminList"),
            Choice(name="Bot status", value="botStatusList"),
            Choice(name="Ban user", value="userBlackList"),
            Choice(name="Ban server", value="serverBlackList"),
        ]
    )
    async def remove(
        self,
        interaction: discord.Interaction,
        key: Choice[str],
        user: Optional[discord.User] = None,
        server: Optional[str] = None,
        status: Optional[str] = None,
    ):
        try:
            if not await UsefulMethods.check_is_guild(interaction):
                return await interaction.response.send_message("Commande indisponible en messages privés.", ephemeral=True)

            member = interaction.user
            assert member is not None
            has_permissions = database.is_admin(member.id) or UsefulMethods.check_is_support_member(member.id)

            if not has_permissions:
                logger.warning(f"[WARNING MODO] Unauthorized remove attempt by: {member.id}")
                return await interaction.response.send_message("Accès refusé.", ephemeral=True)

            if key.value == "adminList":
                if user is None:
                    return await interaction.response.send_message("Veuillez spécifier un utilisateur.", ephemeral=True)

                if user.id == interaction.user.id:
                    return await interaction.response.send_message("Vous ne pouvez pas vous retirer vous-même des administrateurs.", ephemeral=True)

                if database.is_admin(user.id):
                    database.remove_admin(user.id)
                    return await interaction.response.send_message(f"{user.mention} n'est plus administrateur.", ephemeral=True)
                else:
                    return await interaction.response.send_message(f"{user.mention} n'est pas dans la liste des administrateurs.", ephemeral=True)

            elif key.value == "userBlackList":
                if user is None:
                    return await interaction.response.send_message("Veuillez spécifier un utilisateur.", ephemeral=True)

                if database.is_user_banned(user.id):
                    database.unban_user(user.id)
                    return await interaction.response.send_message(f"{user.mention} a été débanni.", ephemeral=True)
                else:
                    return await interaction.response.send_message(f"{user.mention} n'est pas banni.", ephemeral=True)

            elif key.value == "serverBlackList":
                if server is None:
                    return await interaction.response.send_message("Veuillez spécifier l'identifiant du serveur.", ephemeral=True)

                if not server.isdigit():
                    return await interaction.response.send_message(f"L'identifiant `{server}` n'est pas valide.", ephemeral=True)

                guild_id = int(server)
                target_guild = self.bot.get_guild(guild_id)
                guild_name = target_guild.name if target_guild is not None else f"{guild_id}"

                if database.is_server_banned(guild_id):
                    database.unban_server(guild_id)
                    return await interaction.response.send_message(f"Le serveur `{guild_name}` n'est plus banni.", ephemeral=True)
                else:
                    return await interaction.response.send_message(f"Le serveur `{guild_name}` n'est pas dans la liste noire.", ephemeral=True)

            elif key.value == "botStatusList":
                if status is None or not status.strip():
                    return await interaction.response.send_message("Veuillez spécifier le texte du statut.", ephemeral=True)

                status_text = status.strip()

                if status_text in database.get_activities():
                    database.remove_activity(status_text)
                    return await interaction.response.send_message(f"Le statut `{status_text}` a été retiré.", ephemeral=True)
                else:
                    return await interaction.response.send_message(f"Le statut `{status_text}` n'existe pas.", ephemeral=True)

        except ValueError as error:
            logger.error(f"[ERROR MODO] Validation error for key '{key.value}': {error}", exc_info=True)
            await interaction.response.send_message("Valeur fournie invalide.", ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR MODO] Error removing value: {error}", exc_info=True)
            await interaction.response.send_message("Une erreur s'est produite lors de l'exécution de la commande.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Modo(bot))