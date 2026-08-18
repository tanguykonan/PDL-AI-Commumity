# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 30/12/2025
# ==================================================================================
import discord
from typing import Optional
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from app.helps.utils import UsefulMethods
from app.helps.utils import logger, mydecorators
from plugins.integrating.storing.database import database

class Modo(commands.GroupCog, name = "modo"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name = "define", description = "DEVS-> Définir une nouvelle valeur de plus à une clé")
    @app_commands.describe(
        key = 'La clé à modifier',
        user = "Sélectionner l'utilisateur",
        server = "Entrez l'identifiant du serveur",
        status = "Entrez le text du status"
    )
    @app_commands.choices(key =[
        Choice(name = 'Bot admins', value = 'adminList'),
        Choice(name='Bot status', value='botStatusList'),
        Choice(name = 'Ban user', value = 'userBlackList'),
        Choice(name='Ban server', value = 'serverBlackList')
    ])
    async def define(
            self,
            interaction: discord.Interaction,
            key: Choice[str],
            user: Optional[discord.User] = None,
            server: Optional[str] = None,
            status: Optional[str] = None
        ):
        try:
            if not await UsefulMethods.check_is_guild(interaction):
                return await interaction.response.send_message("Tu te fou de ma gueule c'est ca !? Et bien va e faire foutre.")

            member = interaction.user
            assert member is not None
            has_permissions = (
                    database.is_admin(member.id) or
                    UsefulMethods.check_is_support_member(member.id)
            )

            if not has_permissions:
                logger.warning(f"[WARNING DEBUG] Utilisateur non autorisé a tenté de définir une nouvelle valeur à une propriété : {member.id}")
                return await interaction.response.send_message("Mais putain, tu fou quoi toi ? T'en as pas le droit tu m'entent !?", ephemeral=True)

            if key.value == 'adminList':
                if user is None:
                    return await interaction.response.send_message("Tu es une minorité et tu n'es capable passer le compte au paramètre 'user' !", ephemeral=True)
                if user.bot:
                    return await interaction.response.send_message("Oh, nous somme foutu. Tu essaies ce truc sur un bot sérieusement..", ephemeral=True)

                if database.is_admin(user.id):
                    return await interaction.response.send_message(f"EhOh ! {user.mention} est déjà un administrateur à mon avis !", ephemeral=True)
                database.add_admin(user.id)
                return await interaction.response.send_message(f"Super ! donc {user.mention} est désormais un administrateur ? Bravo.", ephemeral=True)

            elif key.value == 'userBlackList':
                if user is None:
                    return await interaction.response.send_message("Tu es une minorité et tu n'es capable passer le compte au paramètre 'user' !", ephemeral=True)
                if database.is_admin(user.id):
                    return await interaction.response.send_message("Tu veux bloquer une minorité !? Alors là tu te fou le doigt h dans l'oeil.", ephemeral=True)

                if database.is_user_banned(user.id):
                    return await  interaction.response.send_message(f"Si seulement !! C'était possible de bannir un banni, dommage pour toi {member.name}.", ephemeral=True)
                database.ban_user(user.id)
                return await  interaction.response.send_message(f"Cool !! Une majorité de moins, dommage pour {user.mention}.", ephemeral=True)

            elif key.value == 'serverBlackList':
                if server is None:
                    return await interaction.response.send_message("Tu es une minorité et tu n'es capable passer l'id du serveur au paramètre 'server' !", ephemeral=True)
                if not server.isdigit():
                    return  await interaction.response.send_message(f"Désolé {member.name}, mais ce putain d'identifiant n'est pas valide ! Ouf.", ephemeral=True)

                guild_id = int(server)
                guild = interaction.guild
                assert  guild is not None
                if guild_id == guild.id:
                    return await interaction.response.send_message(f"Mais {member.name}, tu ne vas quand même pas ban ce serveur..", ephemeral=True)

                guild = self.bot.get_guild(guild_id)
                guild_name = guild.name if guild is not None else f"{guild_id}"

                if database.is_server_banned(guild_id):
                    return await interaction.response.send_message(f"Merci {member.name} mais.., ce serveur ({guild_name}) est déjà ban.", ephemeral=True)
                database.ban_server(guild_id)
                return await interaction.response.send_message(f"Merci {member.name}, tu me libère d'un surplice ({guild_name}).", ephemeral=True)

            elif key.value == 'botStatusList':
                if status is None or not status.strip():
                    return await interaction.response.send_message("Tu es une minorité et tu n'es capable passer du texte au paramètre 'status' !", ephemeral=True)

                status_text = status.strip()
                if len(status_text) > 128:
                    return await interaction.response.send_message(f"Euh, il s'agit d'un status {member.name}, pas de ta vie.", ephemeral=True)

                if status_text in database.get_activities():
                    return await interaction.response.send_message(f"Cette merde '{status_text}' est déjà en status.", ephemeral=True)
                database.add_activity(status_text)
                return await interaction.response.send_message(f"Ok, j'ai ajouté ce bout de merde '{status_text}' en status.", ephemeral=True)

        except ValueError as error:
            logger.error(f"[ERROR MODO]=> Une erreur de validation pour la clé '{key.value}' s'est produite: {error}", exc_info=True)
            return await interaction.response.send_message("Apparent, tu as fournie une valeur de merde difficile à valider.", ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR MODO]=> Une erreur s'est produite lors de l'ajout d'une valeur à la clé : {error}", exc_info=True)
            return await interaction.response.send_message(f"My bad ! Il y a un soucis logique au niveau de cette commande.", ephemeral=True)

    @app_commands.command(name="remove", description="DEVS-> Retirer une des valeurs d'une clé")
    @app_commands.describe(
        key='La clé à modifier',
        user="Sélectionner l'utilisateur",
        server="Entrez l'identifiant du serveur",
        status="Entrez le text du status"
    )
    @app_commands.choices(key=[
        Choice(name='Bot admins', value='adminList'),
        Choice(name='Bot status', value='botStatusList'),
        Choice(name='Ban user', value='userBlackList'),
        Choice(name='Ban server', value='serverBlackList')
    ])
    async def remove(
            self,
            interaction: discord.Interaction,
            key: Choice[str],
            user: Optional[discord.User] = None,
            server: Optional[str] = None,
            status: Optional[str] = None
    ):
        try:
            if not await UsefulMethods.check_is_guild(interaction):
                return await interaction.response.send_message("Tu te fou de ma gueule c'est ca !? Et bien va e faire foutre.")

            member = interaction.user
            assert member is not None
            has_permissions = (
                    database.is_admin(member.id) or
                    UsefulMethods.check_is_support_member(member.id)
            )

            if not has_permissions:
                logger.warning(f"[WARNING DEBUG] Utilisateur non autorisé a tenté de définir une nouvelle valeur à une propriété : {member.id}")
                return await interaction.response.send_message("Mais putain, tu fou quoi toi ? T'en as pas le droit tu m'entent !?", ephemeral=True)

            if key.value == 'adminList':
                if user is None:
                    return await interaction.response.send_message("Tu es une minorité et tu n'es capable passer le compte au paramètre 'user' !", ephemeral=True)

                if user.id == interaction.user.id:
                    return await interaction.response.send_message("Putain, tu veux vraiment te retirer toi-même des admins ? Malin.", ephemeral=True)

                if database.is_admin(user.id):
                    database.remove_admin(user.id)
                    return await interaction.response.send_message(f"Bon, {user.mention} n'est plus un administrateur. Content ?", ephemeral=True)
                else:
                    return await interaction.response.send_message(f"Malheureusement, {user.mention} n'est pas un administrateur. Content ?", ephemeral=True)

            elif key.value == 'userBlackList':
                if user is None:
                    return await interaction.response.send_message("Tu es une minorité et tu n'es capable passer le compte au paramètre 'user' !", ephemeral=True)

                if database.is_user_banned(user.id):
                    database.unban_user(user.id)
                    return await interaction.response.send_message(f"Ok, {user.mention} a été retiré de la blacklist. Il a intérêt à se tenir bien.", ephemeral=True)
                else:
                    return await interaction.response.send_message(f"Désolé mais, {user.mention} n'est pas dans la blacklist. Courage à toi.",ephemeral=True)

            elif key.value == 'serverBlackList':
                if server is None:
                    return await interaction.response.send_message("Tu es une minorité et tu n'es capable passer l'id du serveur au paramètre 'server' !", ephemeral=True)

                if not server.isdigit():
                    return await interaction.response.send_message(f"Désolé {member.name}, mais ce putain d'identifiant n'est pas valide ! Ouf.", ephemeral=True)

                guild_id = int(server)
                guild = self.bot.get_guild(guild_id)
                guild_name = guild.name if guild is not None else f"{guild_id}"

                if database.is_server_banned(guild_id):
                    database.unban_server(guild_id)
                    return await interaction.response.send_message(f"Voilà, le serveur {guild_name} n'est plus blacklisté. Donnons lui une seconde chance.", ephemeral=True)
                else:
                    return await interaction.response.send_message(f"Le serveur {guild_name} n'est pas blacklisté. Il n'auras pas besoin d'une deuxième chance.", ephemeral=True)

            elif key.value == 'botStatusList':
                if status is None or not status.strip():
                    return await interaction.response.send_message("Tu es une minorité et tu n'es capable passer du texte au paramètre 'status' !", ephemeral=True)

                status_text = status.strip()

                if status_text in database.get_activities():
                    database.remove_activity(status_text)
                    return await interaction.response.send_message(f"Parfait, j'ai viré ce status de merde: `{status_text}`.", ephemeral=True)
                else:
                    return await interaction.response.send_message(f"Tu sais, si tu connais pas la liste actuelle, tu peux vérifier avant.", ephemeral=True)

        except ValueError as error:
            logger.error(f"[ERROR MODO]=> Une erreur de validation pour la clé '{key.value}' s'est produite: {error}", exc_info=True)
            await interaction.response.send_message("Apparent, tu as fournie une valeur de merde difficile à valider.", ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR MODO]=> Une erreur s'est produite lors du retrait d'une valeur à la clé : {error}", exc_info=True)
            await interaction.response.send_message("Putain, une erreur de merde s'est produite. Check les logs.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Modo(bot))