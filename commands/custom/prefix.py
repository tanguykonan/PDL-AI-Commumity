"""Prefix-based maintenance and root administration commands (+root)."""

import asyncio
import datetime
import discord
from discord.ext import commands
from discord import TextChannel, Thread
from app.helps.utils import UsefulMethods, logger
from plugins.integrating.storing.database import database


class Root(commands.Cog):
    """Hidden root command suite for bot developers and maintainers."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    async def temp_msg_response(ctx: commands.Context, message: str, delay: int = 5):
        """Send a temporary text response that self-deletes after a delay."""
        response = await ctx.send(message)
        await asyncio.sleep(delay)
        try:
            await response.delete()
        except discord.Forbidden:
            pass

    @staticmethod
    async def temp_embed_response(ctx: commands.Context, embed: discord.Embed, delay: int = 15):
        """Send a temporary embed response that self-deletes after a delay."""
        await ctx.send(embed=embed, delete_after=delay)

    @commands.group()
    async def root(self, ctx: commands.Context):
        """Root command group entrypoint."""
        if ctx.invoked_subcommand is None:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

    @root.command(name="help", help="Display available root commands.")
    async def help(self, ctx: commands.Context):
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            verified = UsefulMethods.check_is_support_member(ctx.author.id)
            if not verified:
                return

            embed = discord.Embed(
                title="Root Commands",
                description=(
                    "`+root bot stats` -> View bot statistics.\n"
                    "`+root bot status` -> List custom status activities.\n"
                    "`+root bot blacklist` -> List blacklisted users and servers.\n"
                    "`+root bot admin` -> List bot administrators.\n"
                    "`+root channel add` -> Add current channel to active list.\n"
                    "`+root channel remove` -> Remove current channel from active list.\n"
                    "`+root broadcast` -> Send announcement to all servers.\n"
                    "`+root setpremium` -> Enable or disable premium for a server.\n"
                    "`+root quit` -> Force the bot to leave a server.\n"
                ),
                color=0x000000,
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            await self.temp_embed_response(ctx, embed=embed)
        except Exception as error:
            logger.error(f"[ERROR PREFIX CMD] Error in root help: {error}", exc_info=True)

    @root.command(name="bot", help="Inspect bot database metrics and lists.")
    async def bot(self, ctx: commands.Context, option: str):
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            verified = UsefulMethods.check_is_support_member(ctx.author.id)
            if not verified:
                return

            options_list = ["stats", "blacklist", "admin", "status"]
            if option not in options_list:
                return

            datas = database.get_all_data()

            if option == "stats":
                statistics = database.get_stats()
                embed_stats = discord.Embed(
                    title="Global Bot Statistics",
                    description=(
                        f"Total Servers: `{statistics['serverNumber']}`\n"
                        f"Total Users: `{statistics['userNumber']}`\n"
                        f"Resolved Queries: `{statistics['queryNumber']}`\n"
                        f"Servers in Memory: `{statistics['serversTracked']}`\n"
                        f"Users in Memory: `{statistics['usersInMemory']}`\n"
                        f"Total Thread Messages: `{statistics['totalMessages']}`\n"
                        f"Total Server Messages: `{statistics['totalServerMessages']}`\n"
                    ),
                    color=0x000000,
                )
                embed_stats.set_thumbnail(url=self.bot.user.display_avatar.url)
                await self.temp_embed_response(ctx, embed=embed_stats)

            elif option == "blacklist":
                users = datas["users"]
                servers = datas["servers"]
                users_blacklist = [user for user in users if database.is_user_banned(user)]
                server_blacklist = [server for server in servers if database.is_server_banned(server)]

                user_blacklist_text = "\n".join(f"`{user}`" for user in users_blacklist) or "None"
                server_blacklist_text = "\n".join(f"`{server}`" for server in server_blacklist) or "None"

                embed_blacklist = discord.Embed(
                    title="Active Blacklists",
                    description=(
                        f"**Banned Users:**\n{user_blacklist_text}\n\n"
                        f"**Banned Servers:**\n{server_blacklist_text}\n"
                    ),
                    color=0x000000,
                )
                embed_blacklist.set_thumbnail(url=self.bot.user.display_avatar.url)
                await self.temp_embed_response(ctx, embed=embed_blacklist)

            elif option == "admin":
                admin_list = datas["bot"]["admins"]
                admin_text = "\n".join(f"`{admin}`" for admin in admin_list) or "None"
                embed_admin = discord.Embed(
                    title="Bot Administrators",
                    description=admin_text,
                    color=0x000000,
                )
                embed_admin.set_thumbnail(url=self.bot.user.display_avatar.url)
                await self.temp_embed_response(ctx, embed=embed_admin)

            elif option == "status":
                status_list = datas["bot"]["activities"]
                status_text = "\n".join(f"`{status}`" for status in status_list) or "None"
                embed_status = discord.Embed(
                    title="Bot Activity Statuses",
                    description=status_text,
                    color=0x000000,
                )
                embed_status.set_thumbnail(url=self.bot.user.display_avatar.url)
                await self.temp_embed_response(ctx, embed=embed_status)

        except Exception as error:
            logger.error(f"[ERROR PREFIX CMD] Error in root bot command: {error}", exc_info=True)

    @commands.guild_only()
    @root.command(name="setpremium", help="Toggle premium status for a server.")
    async def setpremium(self, ctx: commands.Context, server_id: int, action: str):
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            verified = UsefulMethods.check_is_support_member(ctx.author.id)
            if not verified:
                return

            choices = ["true", "false"]
            action = action.lower()
            if action not in choices:
                await self.temp_msg_response(ctx, "Usage : `+root setpremium <server_id> true/false`.")
                return

            guild = self.bot.get_guild(server_id)
            if guild is None:
                await self.temp_msg_response(ctx, f"Serveur `{server_id}` introuvable.")
                return

            state = action == "true"
            database.set_premium(server_id, state)

            label = "activé" if state else "désactivé"
            await self.temp_msg_response(ctx, f"Premium `{label}` pour le serveur `{guild.name}` (`{server_id}`).")

        except Exception as error:
            logger.error(f"[ERROR PREFIX CMD] Error in root setpremium: {error}", exc_info=True)

    @commands.guild_only()
    @root.command(name="channel", help="Add or remove discussion channel.")
    async def server(self, ctx: commands.Context, option: str):
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            verified = UsefulMethods.check_is_support_member(ctx.author.id)
            if not verified:
                return

            choices_list = ["add", "remove"]
            channel = ctx.channel.id
            guild = ctx.guild

            if guild is None or option not in choices_list:
                return

            if option == "add":
                if database.is_channel_authorized(guild.id, channel):
                    await self.temp_msg_response(ctx, "Ce salon est déjà configuré.")
                else:
                    database.add_channel(guild.id, channel)
                    await self.temp_msg_response(ctx, f"Le salon `{channel}` a bien été ajouté.")

            elif option == "remove":
                if database.is_channel_authorized(guild.id, channel):
                    database.remove_channel(guild.id, channel)
                    await self.temp_msg_response(ctx, f"Le salon `{channel}` a été retiré.")
                else:
                    await self.temp_msg_response(ctx, "Ce salon n'était pas configuré.")

        except Exception as err:
            logger.error(f"[ERROR PREFIX CMD] Error in root channel {option}: {err}", exc_info=True)

    @root.command(name="broadcast", help="Broadcast an announcement to all servers.")
    async def broadcast(self, ctx: commands.Context, *, message: str):
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            verified = UsefulMethods.check_is_support_member(ctx.author.id)
            if not verified or len(message) <= 20:
                return

            response = await ctx.send("Envoi de l'annonce en cours...")

            embed = discord.Embed(
                title="📢 Annonce Officielle",
                description=f"> {message}",
                color=0x2B1C19,
                timestamp=datetime.datetime.now(),
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text="PDL-AI Community")

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
                        logger.warning(f"[WARNING PREFIX CMD] Failed broadcast to {channel_id}: {error}", exc_info=True)
                else:
                    fail_broadcast_count += 1

            await response.edit(
                content=(
                    f"**Broadcast terminé**\n"
                    f"Succès: {success_broadcast_count}/{len(self.bot.guilds)} | Échecs: {fail_broadcast_count}"
                )
            )
            await asyncio.sleep(5)
            await response.delete()

        except Exception as err:
            logger.error(f"[ERROR PREFIX CMD] Error during broadcast: {err}", exc_info=True)

    @commands.guild_only()
    @root.command(name="quit", help="Force bot to leave a server.")
    async def quit(self, ctx: commands.Context, server: int = None):
        try:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            verified = UsefulMethods.check_is_support_member(ctx.author.id)
            if not verified:
                return

            if server is None:
                if not ctx.guild:
                    return
                guild = ctx.guild
            else:
                guild = self.bot.get_guild(server)
                if not guild:
                    await self.temp_msg_response(ctx, f"Serveur `{server}` introuvable.")
                    return

            assert guild is not None
            await self.temp_msg_response(ctx, "Départ du serveur dans 5 secondes.", 5)
            await guild.leave()

        except Exception as err:
            logger.error(f"[ERROR PREFIX CMD] Error in root quit: {err}", exc_info=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Root(bot))