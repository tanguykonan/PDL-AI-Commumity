# ==================================================================================
# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 30/12/2025
# ==================================================================================
import re
import asyncio
import discord
import datetime
from itertools import cycle
from colorama import Fore, Style
from settings.config import params
from discord.ext import commands, tasks
from app.core.neurochat import ChatEngine
from app.helps.utils import logger
from app.cluster.ram.ddr.ddr2 import RandomAccessMemory
from plugins.processing.analyzer.ocr import OCRProcessor
from plugins.integrating.storing.database import database
from plugins.processing.agenticRag.ise import InternalSearchEngine

from aiohttp import ClientConnectionResetError
from discord.errors import ConnectionClosed

chat = ChatEngine()
ocr = OCRProcessor()
ise = InternalSearchEngine()
memory = RandomAccessMemory()

bot = None
status = None

@tasks.loop(seconds=params.STATUS_UPDATE_TIME)
async def status_swap():
    """Changer le statut du bot périodiquement"""
    try:
        global status
        activities = database.get_activities()
        if not bot or not bot.is_ready(): return #type:ignore
        if not activities: return

        if not hasattr(status_swap, "cycle") or status_swap.cycle_list != activities:
            status_swap.cycle = cycle(activities)
            status_swap.cycle_list = activities

        current_status = next(status_swap.cycle)
        await bot.change_presence(activity=discord.CustomActivity(current_status)) # type: ignore[name-unresolved]

    except (ClientConnectionResetError, ConnectionClosed) as error:
        logger.warning(f"[WARNING MAIN]-> Connexion fermée lors du changement de statut: {error}", exc_info=True)
        if status_swap.is_running() and (not bot.ws or bot.ws.closed): #type:ignore
            status_swap.cancel()
            logger.warning("[WARNING MAIN]-> La tâche swap status s'est arrêtée: (connexion fermée)", exc_info=True)

    except Exception as error:
        logger.error(f"[ERREUR MAIN]-> Une erreur s'est produite lors de l'exécution de la tache périodique [swap status]: {error}", exc_info=True)

@tasks.loop(minutes=params.META_CLEAR_TIME)
async def clear_inactive_memory():
    """Nettoyer automatiquement les utilisateurs inactifs"""
    try:
        if not bot or not bot.is_ready(): return #type:ignore
        memory.clear_memory()
    except Exception as error:
        logger.error(f"[ERREUR MAIN]-> Une erreur s'est produite lors de l'exécution de la tache périodique [clear inactive users]: {error}", exc_info=True)

def display_banner():
    banner = """
        ██████╗ ██████╗  ██╗         █████╗ ██╗
        ██╔══██╗██╔══██╗ ██║        ██╔══██╗██║
        ██████╔╝██║  ██║ ██║        ███████║██║
        ██╔═══╝ ██║  ██║ ██║        ██╔══██║██║
        ██║     ██████╔╝ ███████╗██╗██║  ██║██║
        ╚═╝     ╚═════╝  ╚══════╝╚═╝╚═╚═╝╚═╝╚═╝
    """
    print(f"\033[31m{banner}\033[0m")

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++++ REGISTRE GÉNERALE DES FONCTIONNALITÉS DU BOT +++++++++++++
def register_commands(bot_instance: commands.Bot):
    try:
        global bot
        bot = bot_instance
        display_banner()
    except Exception as error:
        logger.error(f"[ERREUR MAIN]-> Une erreur s'est produite avec l'assignation du bot : {error}", exc_info=True)

    @status_swap.before_loop
    async def before_status_swap():
        await bot.wait_until_ready()

    @clear_inactive_memory.before_loop
    async def before_clear_inactive_users():
        await bot.wait_until_ready()

    @bot.event # noqa
    async def on_ready():
        try:
            if not status_swap.is_running():
                status_swap.start()

            if not clear_inactive_memory.is_running():
                clear_inactive_memory.start()

        except Exception as errors:
            print(Fore.RED +f"[ERREUR MAIN]-> Une erreur s'est produite lors du démarrage des tâches périodiques: {errors}" + Style.RESET_ALL)

        try:
            client = bot.user
            assert client is not None
            synced = await bot.tree.sync()

            total_users = sum(guild.member_count or 0 for guild in bot.guilds)
            database.update_stat("userNumber", total_users)
            database.update_stat("serverNumber", len(bot.guilds))

            await restore_database()

            print(Fore.CYAN + f"[INFO MAIN]=> {len(synced)} commandes synchronisées !" + Style.RESET_ALL)
            print(Fore.CYAN + f"[INFO MAIN]=> {len(bot.guilds)} serveurs connectés !" + Style.RESET_ALL)
            print(Fore.GREEN + f"[SUCCÈS MAIN]=> {client.name} est prêt et en ligne !\n" + Style.RESET_ALL)

        except Exception as errors:
            print(Fore.RED + f"[ERREUR MAIN]-> Une erreur lors de la synchronisation des commandes slash s'est produite: {errors}" + Style.RESET_ALL)

    #===============================================================
    #===============================================================
    async def _attachment_extractor(attachments: list[discord.Attachment]):
        try:
            extracted_text = []
            for attachment in attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                    ocr_result = await ocr.process_attachment(attachment)
                    if ocr_result.strip():
                        extracted = f"\n[Texte détecté dans l'image: {ocr_result}]"
                        extracted_text.append(extracted)
                    else:
                        extracted = f"\n[Aucun texte détecté dans l'image]"
                        extracted_text.append(extracted)
            return "".join(extracted_text)
        except Exception as err:
            logger.error(f"[ERREUR MAIN]=> L'extraction du contenue des images est rencontre un bug: {err}", exc_info=True)
            return f"\n[L'analyse de l'image a échouée]"
    #======================================================================================================================
    #======================================================================================================================
    async def save_stats():
        def _save():
            database.increment_stat("queryNumber")
            database.update_stat("usersInMemory", memory.stats()["users_in_memory"])
            database.update_stat("serversTracked", memory.stats()["servers_tracked"])
            database.update_stat("totalMessages", memory.stats()["total_messages"])
            database.update_stat("totalServerMessages", memory.stats()["total_server_msgs"])
        await asyncio.to_thread(_save)
    #======================================================================================================================

    @bot.event #type:ignore
    async def on_message(message):

        # ── Vérifications des droits d'action ──────────────────────────────────────────────
        if message.author.bot: return
        
        def _check_permissions():
            if database.is_user_banned(message.author.id): return False
            if message.guild:
                if database.is_server_banned(message.guild.id): return False
                # BUG FIX : Utiliser AND (et non OR) — un admin peut parler partout,
                # un utilisateur normal doit être dans un salon autorisé.
                channel_ok = database.is_channel_authorized(message.guild.id, message.channel.id)
                user_is_admin = database.is_admin(message.author.id)
                if not channel_ok and not user_is_admin: return False
                return True
            else:
                # BUG FIX : Ne pas faire return après process_commands en DM,
                # laisser la logique IA s'exécuter pour les admins autorisés.
                return database.is_admin(message.author.id)

        if not await asyncio.to_thread(_check_permissions): return

        # ── Définition des attribués d'instance ──────────────────────────────────────────────
        user_id = str(message.author.id)
        username = message.author.name
        user_message = message.content.strip()
        server_id = str(message.guild.id)

        # ── Action de login serveur ──────────────────────────────────────────────
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
            # BUG FIX : Ne pas interrompre le traitement sur une erreur RAG —
            # le stockage est secondaire, l'IA doit continuer à répondre.
            logger.error(f"[ERROR MAIN]-> Une erreur c'est produite durant l'écoute du serveur en rag: {err}", exc_info=True)

        # ── Permissions d'intervention ──────────────────────────────────────────────
        mention_true = bot.user.mentioned_in(message) #type:ignore
        call_true = bool(re.search(rf'\b{re.escape(params.NAME.lower())}\b', user_message.lower()))
        reference_true = (message.reference and message.reference.resolved and message.reference.resolved.author == bot.user)

        # ── Gestion de l'appel au module de génération ──────────────────────────────────────────────
        if mention_true or call_true or reference_true:
            """Démarrage du processus d'intéraction entre le bot et les utilisateurs"""
            try:

                memory.add_server_message(server_id, user_id, username, str(message.channel.id), getattr(message.channel, "name", "dm"), user_message)
                memory.manage(user_id, user_message, role = 'user', username=username)

                history = memory.build_context(user_id, server_id=server_id, channel_id=str(message.channel.id), username=username)

                async with message.channel.typing():
                    await asyncio.sleep(params.FLOWTYPE_TIME)
                    response = await chat.generate_response(
                        conversation_history=history,
                        username=username,
                        server_id=server_id,
                        bot=bot,
                        message=message
                    )
                if response is not None:
                    memory.manage(user_id, response, role = 'assistant')
                    await asyncio.to_thread(memory.save_to_file)
                    await save_stats()
                    await message.reply(response)
                else:
                    await message.reply(f"Je ne suis pas d'humeur {username}. Le mieux c'est que tu reviennes plus tard.")

                return

            except Exception as errors:
                logger.error(f"[ERROR MAIN]=> Une erreur s'est produite au niveau du système d'échange: {errors} ", exc_info=True)
                await message.reply("Une erreur s'est produite. Contacte un admin si ça persiste.")
                return

        await bot.process_commands(message)

    @bot.event #type:ignore
    async def on_guild_join(guild):
        try:
            if database.is_server_banned(guild.id):
                await guild.leave()
                return

            total_users = sum(guild.member_count or 0 for guild in bot.guilds)
            database.update_stat("userNumber", total_users)
            database.update_stat("serverNumber", len(bot.guilds))

            invite_url = "Pas d'invitation possible"
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).create_instant_invite:
                    try:
                        invite = await channel.create_invite(max_age=0, max_uses=0)
                        invite_url = invite.url
                        break
                    except discord.Forbidden:
                        continue

            owner = guild.owner.mention if guild.owner else f"ID: {guild.owner_id}" #type:ignore
            embed_join = discord.Embed(
                title=f"PDL a rejoint {guild.name}",
                description=f"""
                    Fondateur: `{owner}`
                    Nombre de membres: `{guild.member_count}`
                    Lien d'invitation: `{invite_url}`
                """,
                colour=discord.Colour.dark_green(),
                timestamp=datetime.datetime.now(),
            )
            channel_id = int(params.SUPPORT_CHANNEL)
            channel = bot.get_channel(channel_id)
            if isinstance(channel, discord.TextChannel):
                await channel.send(embed=embed_join)
            else:
                logger.error(f"[ERREUR MAIN]=> Channel de support introuvable (ID: {channel_id})")

        except Exception as errors:
            logger.error(f"[ERREUR MAIN]=> Une erreur s'est produite dans on_guild_join: {errors}", exc_info=True)

    @bot.event #type:ignore
    async def on_guild_remove(guild):
        try:
            if database.is_server_banned(guild.id): return

            total_users = sum(guild.member_count or 0 for guild in bot.guilds)
            database.update_stat("userNumber", total_users)
            database.update_stat("serverNumber", len(bot.guilds))

            owner = guild.owner.mention if guild.owner else f"ID: {guild.owner_id}" #type:ignore
            embed_remove = discord.Embed(
                title=f"PDL a quitté {guild.name}",
                description=f"""
                    Fondateur: `{owner}`
                    Nombre de membres: `{guild.member_count}`
                """,
                colour=discord.Colour.dark_red(),
                timestamp=datetime.datetime.now(),
            )
            channel_id = int(params.SUPPORT_CHANNEL)
            channel = bot.get_channel(channel_id)
            if isinstance(channel, discord.TextChannel):
                await channel.send(embed=embed_remove)
            else:
                logger.error(f"[ERREUR MAIN]-> Channel de support introuvable (ID: {channel_id})")

        except Exception as errors:
            logger.error(f"[ERREUR MAIN]-> Une erreur s'est produite dans on_guild_remove: {errors}", exc_info=True)

    @bot.event #type:ignore
    async def on_socket_response(payload):
        if payload.get("t") in ("VOICE_STATE_UPDATE", "VOICE_SERVER_UPDATE"):
            music_cog = bot.get_cog("music")
            if music_cog and hasattr(music_cog, "lavalink_manager"):
                manager = music_cog.lavalink_manager
                if manager and manager.client:
                    await manager.client.voice_update_handler(payload)

    @bot.event #type:ignore
    async def on_resumed():
        """Redémarrer les tâches après une reconnexion"""
        if not status_swap.is_running():
            logger.warning("[INFO MAIN]=> Redémarrage de status_swap après reconnexion")
            status_swap.start()

    @bot.event #type:ignore
    async def on_command_error(_, errors):
        if isinstance(errors, commands.CommandNotFound):
            return
        logger.error(f"[ERREUR COMMANDE]-> {errors}", exc_info=True)