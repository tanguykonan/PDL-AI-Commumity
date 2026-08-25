"""Core bot orchestration: event listeners, presence loops, and message dispatch."""

import re
import asyncio
import datetime
from itertools import cycle
import discord
from discord.ext import commands, tasks
from colorama import Fore, Style
from aiohttp import ClientConnectionResetError
from discord.errors import ConnectionClosed

from settings.config import params
from app.core.neurochat import ChatEngine
from app.helps.utils import logger
from app.cluster.ram.ddr.ddr2 import RandomAccessMemory
from plugins.processing.analyzer.ocr import OCRProcessor
from plugins.integrating.storing.database import database
from plugins.processing.agenticRag.ise import InternalSearchEngine

chat = ChatEngine()
ocr = OCRProcessor()
ise = InternalSearchEngine()
memory = RandomAccessMemory()

bot = None
status = None


@tasks.loop(seconds=params.STATUS_UPDATE_TIME)
async def status_swap():
    """Periodically rotate the bot's custom Discord activity status."""
    try:
        global status
        activities = database.get_activities()
        if not bot or not bot.is_ready():
            return
        if not activities:
            return

        if not hasattr(status_swap, "cycle") or status_swap.cycle_list != activities:
            status_swap.cycle = cycle(activities)
            status_swap.cycle_list = activities

        current_status = next(status_swap.cycle)
        await bot.change_presence(activity=discord.CustomActivity(current_status))

    except (ClientConnectionResetError, ConnectionClosed) as error:
        logger.warning(f"[WARNING MAIN] Connection closed during presence swap: {error}", exc_info=True)
        if status_swap.is_running() and (not bot.ws or bot.ws.closed):
            status_swap.cancel()
            logger.warning("[WARNING MAIN] Presence swap task stopped (connection closed).", exc_info=True)

    except Exception as error:
        logger.error(f"[ERROR MAIN] Error in status_swap loop: {error}", exc_info=True)


@tasks.loop(minutes=params.META_CLEAR_TIME)
async def clear_inactive_memory():
    """Periodically purge inactive users from memory cache."""
    try:
        if not bot or not bot.is_ready():
            return
        memory.clear_memory()
    except Exception as error:
        logger.error(f"[ERROR MAIN] Error in clear_inactive_memory loop: {error}", exc_info=True)


def display_banner():
    """Display startup ASCII logo."""
    banner = """
        ██████╗ ██████╗  ██╗         █████╗ ██╗
        ██╔══██╗██╔══██╗ ██║        ██╔══██╗██║
        ██████╔╝██║  ██║ ██║        ███████║██║
        ██╔═══╝ ██║  ██║ ██║        ██╔══██║██║
        ██║     ██████╔╝ ███████╗██╗██║  ██║██║
        ╚═╝     ╚═════╝  ╚══════╝╚═╝╚═╚═╝╚═╝╚═╝
    """
    print(f"\033[31m{banner}\033[0m")


def register_commands(bot_instance: commands.Bot):
    """Register core event handlers and start background loops."""
    try:
        global bot
        bot = bot_instance
        display_banner()
    except Exception as error:
        logger.error(f"[ERROR MAIN] Failed to assign bot instance: {error}", exc_info=True)

    @status_swap.before_loop
    async def before_status_swap():
        await bot.wait_until_ready()

    @clear_inactive_memory.before_loop
    async def before_clear_inactive_users():
        await bot.wait_until_ready()

    @bot.event
    async def on_ready():
        try:
            if not status_swap.is_running():
                status_swap.start()

            if not clear_inactive_memory.is_running():
                clear_inactive_memory.start()

        except Exception as errors:
            print(Fore.RED + f"[ERROR MAIN] Failed to start periodic tasks: {errors}" + Style.RESET_ALL)

        try:
            client = bot.user
            assert client is not None
            synced = await bot.tree.sync()

            total_users = sum(guild.member_count or 0 for guild in bot.guilds)
            database.update_stat("userNumber", total_users)
            database.update_stat("serverNumber", len(bot.guilds))

            print(Fore.CYAN + f"[INFO MAIN] {len(synced)} slash commands synchronized." + Style.RESET_ALL)
            print(Fore.CYAN + f"[INFO MAIN] {len(bot.guilds)} connected guilds." + Style.RESET_ALL)
            print(Fore.GREEN + f"[SUCCESS MAIN] {client.name} is ready and online.\n" + Style.RESET_ALL)

        except Exception as errors:
            print(Fore.RED + f"[ERROR MAIN] Error synchronizing slash commands: {errors}" + Style.RESET_ALL)

    async def _attachment_extractor(attachments: list[discord.Attachment]) -> str:
        """Extract text from supported image attachments using OCR."""
        try:
            extracted_text = []
            for attachment in attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                    ocr_result = await ocr.process_attachment(attachment)
                    if ocr_result.strip():
                        extracted = f"\n[Detected text in image: {ocr_result}]"
                        extracted_text.append(extracted)
                    else:
                        extracted = "\n[No text detected in image]"
                        extracted_text.append(extracted)
            return "".join(extracted_text)
        except Exception as err:
            logger.error(f"[ERROR MAIN] OCR image extraction failed: {err}", exc_info=True)
            return "\n[Image analysis failed]"

    async def save_stats():
        """Update system and memory statistics in database."""
        def _save():
            database.increment_stat("queryNumber")
            database.update_stat("usersInMemory", memory.stats()["users_in_memory"])
            database.update_stat("serversTracked", memory.stats()["servers_tracked"])
            database.update_stat("totalMessages", memory.stats()["total_messages"])
            database.update_stat("totalServerMessages", memory.stats()["total_server_msgs"])
        await asyncio.to_thread(_save)

    @bot.event
    async def on_message(message: discord.Message):
        """Process incoming messages and trigger AI conversation if mentioned."""
        if message.author.bot:
            return

        def _check_permissions():
            if database.is_user_banned(message.author.id):
                return False
            if message.guild:
                if database.is_server_banned(message.guild.id):
                    return False
                channel_ok = database.is_channel_authorized(message.guild.id, message.channel.id)
                user_is_admin = database.is_admin(message.author.id)
                if not channel_ok and not user_is_admin:
                    return False
                return True
            else:
                return database.is_admin(message.author.id)

        if not await asyncio.to_thread(_check_permissions):
            return

        user_id = str(message.author.id)
        username = message.author.name
        user_message = message.content.strip()
        server_id = str(message.guild.id) if message.guild else "dm"

        # Log server message for local RAG context
        if message.guild:
            try:
                if message.attachments:
                    extracted_text = await _attachment_extractor(message.attachments)
                    user_message += extracted_text
                data = {
                    "channel_name": message.channel.name,
                    "author_name": message.author.name,
                    "reply_to": message.reference.resolved.author.name if message.reference and message.reference.resolved else None,
                    "content": user_message,
                    "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                }
                await ise.store_rag_data(server_id, data)
            except Exception as err:
                logger.error(f"[ERROR MAIN] Failed to store RAG log data: {err}", exc_info=True)

        mention_true = bot.user.mentioned_in(message)
        call_true = bool(re.search(rf"\b{re.escape(params.NAME.lower())}\b", user_message.lower()))
        reference_true = (message.reference and message.reference.resolved and message.reference.resolved.author == bot.user)

        # Trigger conversational engine if mentioned or addressed
        if mention_true or call_true or reference_true:
            try:
                memory.add_server_message(server_id, user_id, username, str(message.channel.id), getattr(message.channel, "name", "dm"), user_message)
                memory.manage(user_id, user_message, role="user", username=username)

                history = memory.build_context(user_id, server_id=server_id, channel_id=str(message.channel.id), username=username)

                async with message.channel.typing():
                    await asyncio.sleep(params.FLOWTYPE_TIME)
                    response = await chat.generate_response(
                        conversation_history=history,
                        username=username,
                        server_id=server_id,
                        bot=bot,
                        message=message,
                    )
                if response is not None:
                    memory.manage(user_id, response, role="assistant")
                    await asyncio.to_thread(memory.save_to_file)
                    await save_stats()
                    await message.reply(response)
                else:
                    await message.reply(f"Je ne suis pas d'humeur {username}. Reviens plus tard.")
                return

            except Exception as errors:
                logger.error(f"[ERROR MAIN] Error in conversation handler: {errors}", exc_info=True)
                await message.reply("Une erreur s'est produite. Contacte un administrateur si le problème persiste.")
                return

        await bot.process_commands(message)

    @bot.event
    async def on_guild_join(guild: discord.Guild):
        """Handle new guild joins."""
        try:
            if database.is_server_banned(guild.id):
                await guild.leave()
                return

            total_users = sum(g.member_count or 0 for g in bot.guilds)
            database.update_stat("userNumber", total_users)
            database.update_stat("serverNumber", len(bot.guilds))

            invite_url = "No invite available"
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).create_instant_invite:
                    try:
                        invite = await channel.create_invite(max_age=0, max_uses=0)
                        invite_url = invite.url
                        break
                    except discord.Forbidden:
                        continue

            owner = guild.owner.mention if guild.owner else f"ID: {guild.owner_id}"
            embed_join = discord.Embed(
                title=f"Joined {guild.name}",
                description=f"Owner: `{owner}`\nMembers: `{guild.member_count}`\nInvite: `{invite_url}`",
                colour=discord.Colour.dark_green(),
                timestamp=datetime.datetime.now(),
            )
            channel_id = int(params.SUPPORT_CHANNEL) if params.SUPPORT_CHANNEL else None
            if channel_id:
                channel = bot.get_channel(channel_id)
                if isinstance(channel, discord.TextChannel):
                    await channel.send(embed=embed_join)

        except Exception as errors:
            logger.error(f"[ERROR MAIN] Error in on_guild_join: {errors}", exc_info=True)

    @bot.event
    async def on_guild_remove(guild: discord.Guild):
        """Handle guild removal."""
        try:
            if database.is_server_banned(guild.id):
                return

            total_users = sum(g.member_count or 0 for g in bot.guilds)
            database.update_stat("userNumber", total_users)
            database.update_stat("serverNumber", len(bot.guilds))

            owner = guild.owner.mention if guild.owner else f"ID: {guild.owner_id}"
            embed_remove = discord.Embed(
                title=f"Left {guild.name}",
                description=f"Owner: `{owner}`\nMembers: `{guild.member_count}`",
                colour=discord.Colour.dark_red(),
                timestamp=datetime.datetime.now(),
            )
            channel_id = int(params.SUPPORT_CHANNEL) if params.SUPPORT_CHANNEL else None
            if channel_id:
                channel = bot.get_channel(channel_id)
                if isinstance(channel, discord.TextChannel):
                    await channel.send(embed=embed_remove)

        except Exception as errors:
            logger.error(f"[ERROR MAIN] Error in on_guild_remove: {errors}", exc_info=True)

    @bot.event
    async def on_socket_response(payload: dict):
        """Forward voice socket packets to Lavalink manager."""
        if payload.get("t") in ("VOICE_STATE_UPDATE", "VOICE_SERVER_UPDATE"):
            music_cog = bot.get_cog("music")
            if music_cog and hasattr(music_cog, "lavalink_manager"):
                manager = music_cog.lavalink_manager
                if manager and manager.client:
                    await manager.client.voice_update_handler(payload)

    @bot.event
    async def on_resumed():
        """Restart background tasks after Discord gateway reconnection."""
        if not status_swap.is_running():
            logger.warning("[INFO MAIN] Resuming status_swap after reconnection.")
            status_swap.start()

    @bot.event
    async def on_command_error(_, errors):
        """Global command error logger."""
        if isinstance(errors, commands.CommandNotFound):
            return
        logger.error(f"[COMMAND ERROR] {errors}", exc_info=True)