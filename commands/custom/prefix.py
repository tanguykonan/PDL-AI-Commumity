# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 09/01/2026
# ==================================================================================
import asyncio
import discord
import datetime
from discord.ext import commands
from app.helps.utils import logger
from discord import TextChannel, Thread
from app.helps.utils import UsefulMethods
from plugins.integrating.storing.database import database

class Root(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    async def temp_msg_response(ctx, message: str, delay: int = 5):
        response = await ctx.send(message)
        await asyncio.sleep(delay)
        try:
            await response.delete()
        except discord.Forbidden: pass

    @staticmethod
    async def temp_embed_response(ctx, embed, delay: int = 15):
        await ctx.send(embed=embed, delete_after=delay)

    @commands.group()
    async def root(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.message.delete()

    @root.command(name="help", help="Afficher les options disponibles")
    async def help(self, ctx: commands.Context):
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden: pass

            verified = UsefulMethods.check_is_support_member(ctx.author.id)
            if verified:
                embed = discord.Embed(
                    title=f"Les options root disponibles",
                    description=(
                        f"`+root bot stats` -> Consulter les statistiques du bot.\n"
                        f"`+root bot status` -> Lister les status du bot.\n"
                        f"`+root bot blacklist` -> Lister les blacklist du bot.\n"
                        f"`+root bot admin` -> Lister les administrateurs du bot.\n"
                        f"`+root channel add` -> Ajouter un channel à prendre en compte.\n"
                        f"`+root channel remove` -> Rétirer un channel à prendre en compte.\n"
                        f"`+root broadcast` -> Envoyer une annonce dans tous les serveurs. `prudence`\n"
                        f"`+root setpremium` -> Activer ou désactiver le premium d'un serveur (server_id + true / false).\n"
                        f"`+root quit` -> Auto éjection du bot.\n"
                    ),
                    color=0x000000
                )
                embed.set_thumbnail(url=self.bot.user.display_avatar.url) #type:ignore
                await self.temp_embed_response(ctx, embed=embed)
            else: return
        except Exception as error:
            logger.error(f"[ERROR PREFIX CMD]-> Une erreur s'est produite lors de l'affichage des options caché: {error}", exc_info=True)

    @root.command(name="bot", help="Afficher les des commandes")
    async def bot(self, ctx: commands.Context, option: str):
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden: pass

            verified = UsefulMethods.check_is_support_member(ctx.author.id)
            if not verified: return

            options_list = ['stats', 'blacklist', 'admin', 'status']
            if option not in options_list: return

            datas = database.get_all_data()

            if option == options_list[0]:
                statistics = database.get_stats()
                embed_stats = discord.Embed(
                    title=f"Le statistiques global sont:",
                    description=(
                        f"Nombre total de serveurs: `{statistics['serverNumber']}`\n"
                        f"Nombre total d'utilisateur: `{statistics['userNumber']}`\n"
                        f"Nombre de requêtes résolues: `{statistics['queryNumber']}`\n"
                        f"Nombre de serveurs en memoire: `{statistics['serversTracked']}`\n"
                        f"Nombre d'utilisateur en memoire: `{statistics['usersInMemory']}`\n"
                        f"Nombre total de thread en memoire: `{statistics['totalMessages']}`\n"
                        f"Nombre de thread serveur en memoire: `{statistics['totalServerMessages']}`\n"
                    ),
                    color=0x000000
                )
                embed_stats.set_thumbnail(url=self.bot.user.display_avatar.url) #type:ignore
                await self.temp_embed_response(ctx, embed=embed_stats)

            elif option == options_list[1]:
                users = datas["users"]
                servers = datas["servers"]
                users_blacklist = []
                server_blacklist = []
                for user in users:
                    if database.is_user_banned(user):
                        users_blacklist.append(user)
                for server in servers:
                    if database.is_server_banned(server):
                        server_blacklist.append(server)

                user_blacklist_text = "\n".join(f"`{user}`" for user in users_blacklist)
                server_blacklist_text = "\n".join(f"`{server}`" for server in server_blacklist)

                embed_blacklist = discord.Embed(
                    title=f"Le bot blacklist disponible",
                    description=(
                        f"**- Liste des utilisateurs bannies**:\n"
                        f"{user_blacklist_text}\n"
                        f"**- Liste des serveurs bannies**:\n"
                        f"{server_blacklist_text}\n"
                    ),
                    color=0x000000
                )
                embed_blacklist.set_thumbnail(url=self.bot.user.display_avatar.url) #type:ignore
                await self.temp_embed_response(ctx, embed=embed_blacklist)

            elif option == options_list[2]:
                admin_list = datas["bot"]["admins"]
                admin_text = "\n".join(f"`{admin}`" for admin in admin_list)
                embed_admin = discord.Embed(
                    title=f"Le bot administrateur disponible",
                    description=admin_text,
                    color=0x000000
                )
                embed_admin.set_thumbnail(url=self.bot.user.display_avatar.url) #type:ignore
                await self.temp_embed_response(ctx, embed=embed_admin)

            elif option == options_list[3]:
                status_list = datas["bot"]["activities"]
                status_text = "\n".join(f"`{status}`" for status in status_list)
                embed_status = discord.Embed(
                    title=f"Le bot status disponible",
                    description=status_text,
                    color=0x000000
                )
                embed_status.set_thumbnail(url=self.bot.user.display_avatar.url) #type:ignore
                await self.temp_embed_response(ctx, embed=embed_status)

        except Exception as error:
            logger.error(f"[ERROR PREFIX CMD]-> Une erreur s'est produite avec la commande [+root bot]: {error}", exc_info=True)

    @commands.guild_only()
    @root.command(name="setpremium", help="Activer ou désactiver le premium d'un serveur")
    async def setpremium(self, ctx: commands.Context, server_id: int, action: str):
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            verified = UsefulMethods.check_is_support_member(ctx.author.id)
            if not verified: return

            choices = ["true", "false"]
            action = action.lower()
            if action not in choices:
                await self.temp_msg_response(ctx, "Utilise `true` ou `false`.")
                return

            guild = self.bot.get_guild(server_id)
            if guild is None:
                await self.temp_msg_response(ctx, f"Le serveur `{server_id}` est introuvable.")
                return

            state = action == "true"
            database.set_premium(server_id, state)

            label = "activé" if state else "désactivé"
            await self.temp_msg_response(ctx, f"Premium `{label}` pour le serveur `{guild.name}` (`{server_id}`).")

        except Exception as error:
            logger.error(f"[ERROR PREFIX CMD]-> Une erreur s'est produite avec la commande [+root setpremium]: {error}",  exc_info=True)

    @commands.guild_only()
    @root.command(name="channel", help="Gérer les salons authorisés")
    async def server(self, ctx: commands.Context, option: str):
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden: pass

            verified = UsefulMethods.check_is_support_member(ctx.author.id)
            if not verified: return

            choices_list = ['add', 'remove']

            channel = ctx.channel.id
            guild = ctx.guild

            if guild is None: return
            if option not in choices_list: return


            if option == choices_list[0]:
                if database.is_channel_authorized(guild.id, channel):
                    await self.temp_msg_response(ctx, f'Ce salon est déjà.')
                else:
                    database.add_channel(guild.id, channel)
                    await self.temp_msg_response(ctx, f'{channel} a bien été ajoutée.')

            elif option == choices_list[1]:
                if database.is_channel_authorized(guild.id, channel):
                    database.remove_channel(guild.id, channel)
                    await self.temp_msg_response(ctx, f"Ce salon ne sera plus pris en compte.")

                else:
                    await self.temp_msg_response(ctx, f"Désolé mais ce salon n'à jamais été pris en compte..")

        except Exception as err:
            logger.error(f"[ERROR PREFIX CMD]-> Une erreur s'est produite lors d'une action root de {option}: {err}", exc_info=True)

    @root.command(name="broadcast", help="Envoyer une annonce dans tous les serveurs")
    async def broadcast(self, ctx: commands.Context, *, message: str):
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden: pass

            verified = UsefulMethods.check_is_support_member(ctx.author.id)
            if not verified: return
            if len(message) <= 20: return

            response = await ctx.send("Ok ! L'envoi du broadcast en cours...")

            embed = discord.Embed(
                title="<a:alert:1464440414378659945> Annonce Officielle",
                description=f"> {message}",
                color=0x2B1C19,
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url) #type:ignore
            embed.set_footer(text=f"{ctx.author.display_name} 2025 PDL-AI. Tous droits réservés")

            success_broadcast_count = 0
            fail_broadcast_count = 0
            first_authorized_channels_list = []
            datas = database.get_all_data()
            for server in datas["servers"]:
                if self.bot.get_guild(int(server)):
                    authorized_channels = datas["servers"][server].get("authorizedChannels", [])
                    if authorized_channels:
                        first_authorized_channels_list.append(int(authorized_channels[0]))

            for channel_id in first_authorized_channels_list:
                channel = self.bot.get_channel(channel_id)
                if isinstance(channel, (TextChannel, Thread)):
                    try:
                        if channel.permissions_for(channel.guild.me).send_messages:
                            await channel.send(embed=embed)
                            success_broadcast_count += 1
                        else:
                            fail_broadcast_count += 1
                    except Exception as error:
                        fail_broadcast_count += 1
                        logger.warning(f"[WARNING PREFIX CMD]-> La raison de l'échec de l'envoie du broadcast est: {error}", exc_info=True)
                else:
                    fail_broadcast_count += 1

            await response.edit(
                content=f"**Broadcast terminé**\n"
                        f"Succès: {success_broadcast_count}/{len(self.bot.guilds)} | Échecs: {fail_broadcast_count}"
            )
            await asyncio.sleep(5)
            await response.delete()

        except Exception as err:
            logger.error(f"[ERROR PREFIX CMD]-> Une grosse erreur s'est produite lors de l'envoie du message broadcast: {err}", exc_info=True)

    @commands.guild_only()
    @root.command(name="quit", help="Auto éjecter le bot du serveur")
    async def quit(self, ctx: commands.Context, server: int=None):
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden: pass

            verified = UsefulMethods.check_is_support_member(ctx.author.id)
            if not verified: return
            if server is None:
                if not ctx.guild: return
                guild = ctx.guild
            else:
                guild = self.bot.get_guild(server)
                if not guild:
                    await self.temp_msg_response(ctx, f"serveur `{server}` introuvable 👀.")
                    return
            assert guild is not None
            await self.temp_msg_response(ctx, "Je quitte ce serveur dans 5 secondes.👋", 5)
            await guild.leave()

        except Exception as err:
            logger.error(f"[ERROR PREFIX CMD]-> Une erreur s'est produite lors de l'auto quit: {err}", exc_info=True)
            await self.temp_msg_response(ctx, f"Petite erreur, consulte `debug error` {ctx.author.display_name}")
            return

async def setup(bot: commands.Bot):
    await bot.add_cog(Root(bot))