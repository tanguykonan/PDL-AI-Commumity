# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 30/12/2025
# ==================================================================================
import asyncio
import discord
import lavalink
from app.helps.utils import logger
from settings.config import params
from typing import Optional, List, Dict, Any

# noinspection PyUnresolvedReferences
class LavalinkVoiceClient(discord.VoiceProtocol):
    """VoiceProtocol qui relaie proprement les voice updates à Lavalink"""
    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        super().__init__(client, channel)
        self.client = client
        self.channel: Optional[discord.abc.Connectable] = channel
        self.guild_id = channel.guild.id
        self._destroyed = False

        if not hasattr(self.client, 'lavalink'):
            self.client.lavalink = lavalink.Client(client.user.id)
        self.lavalink = self.client.lavalink

    def is_connected(self) -> bool:
        return self.channel is not None and not self._destroyed

    async def on_voice_server_update(self, data):
        lavalink_data = {'t': 'VOICE_SERVER_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)  # type:ignore

    async def on_voice_state_update(self, data):
        channel_id = data.get('channel_id')
        if not channel_id:
            await self._destroy()
            return

        self.channel = self.client.get_channel(int(channel_id))  # type:ignore
        lavalink_data = {'t': 'VOICE_STATE_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)  # type:ignore

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False) -> None:
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def disconnect(self, *, force: bool = False) -> None:
        player = None
        if self.channel:
            player = self.lavalink.player_manager.get(self.channel.guild.id)

        if not force and (not player or not getattr(player, 'is_connected', False)):
            return

        self._destroyed = True
        if self.channel:
            await self.channel.guild.change_voice_state(channel=None)
        self.channel = None

        if player:
            player.channel_id = None
            try:
                await self.lavalink.player_manager.destroy(self.guild_id)
            except Exception as error:
                logger.error(f"[ERROR LAVALINK]-> Erreur lors de la destruction du player: {error}", exc_info=True)
                print(f"[ERROR LAVALINK]-> Erreur lors de la destruction du player: {error}")

    async def _destroy(self):
        if self._destroyed:
            return
        self._destroyed = True
        try:
            await self.lavalink.player_manager.destroy(self.guild_id)
        except Exception as error:
            logger.error(f"[ERROR LAVALINK]-> Destroy: {error}", exc_info=True)
            print(f"[ERROR LAVALINK]-> Destroy: {error}")


# noinspection PyUnresolvedReferences
class LavalinkManager:
    def __init__(
        self,
        connection_timeout: int = params.CONNEXION_TIMEOUT,
        retry_attempts: int = params.RETRY_ATTEMPTS,
        healthcheck_interval: int = params.HEALTHCHECK_INTERVAL
    ):
        self.client: Optional[lavalink.Client] = None
        self.connection_timeout = connection_timeout
        self.retry_attempts = retry_attempts
        self.healthcheck_interval = healthcheck_interval
        self.healthcheck_task: Optional[asyncio.Task] = None
        self.is_initialized = False
        self.servers = self._load_server_configs()

    @staticmethod
    def _load_server_configs() -> List[Dict[str, Any]]:
        configs: List[Dict[str, Any]] = []

        hosts = [
            (params.LAVALINK_HOST, "Server1"),
        ]

        for host, identifier in hosts:
            try:
                if not host or not host.strip():
                    logger.warning(f"[WARNING LAVALINK]-> {identifier} ignoré (host non défini)")
                    print(f"[WARNING LAVALINK]-> {identifier} ignoré (host non défini)")
                    continue

                configs.append({
                    "host": host.strip(),
                    "port": int(params.LAVALINK_PORT),
                    "password": params.LAVALINK_PASS,
                    "identifier": identifier,
                    "secure": False
                })

            except (TypeError, ValueError) as error:
                logger.error(f"[ERROR LAVALINK]-> Config {identifier}: {error}")
                print(f"[ERROR LAVALINK]-> Config {identifier}: {error}")

        return configs

    async def connect_nodes(self, bot: discord.Client) -> bool:
        try:
            if not bot.is_ready():
                await bot.wait_until_ready()

            if not self.client:
                self.client = lavalink.Client(bot.user.id)
                self.client.add_event_hooks(self)
                bot.lavalink = self.client
                bot.add_listener(self.client.voice_update_handler, 'on_socket_response')

            connected = 0
            for server in self.servers:
                if await self._connect_single_node(server):
                    connected += 1

            if connected == 0:
                logger.error("[ERROR LAVALINK]-> Aucun nœud connecté")
                print("[ERROR LAVALINK]-> Aucun nœud connecté")
                return False

            self.is_initialized = True

            if not self.healthcheck_task or self.healthcheck_task.done():
                self.healthcheck_task = asyncio.create_task(self._healthcheck_loop())
            return True

        except Exception as error:
            logger.error(f"[ERROR LAVALINK]-> Connexion globale: {error}", exc_info=True)
            print(f"[ERROR LAVALINK]-> Connexion globale: {error}")
            return False

    async def _connect_single_node(self, server: Dict[str, Any]) -> bool:
        identifier = server["identifier"]
        # noinspection PyUnresolvedReferences
        existing_node = None
        for node in self.client.nodes:
            if node.name == identifier:
                existing_node = node
                break

        if existing_node and existing_node.available:
            print(f'[INFO LAVALINK]-> {identifier} déjà connecté')
            return True

        for attempt in range(1, self.retry_attempts + 1):
            try:
                if not existing_node and self.client:
                    self.client.add_node(
                        host=server["host"],
                        port=server["port"],
                        password=server["password"],
                        region="eu",
                        name=identifier,
                        ssl=server["secure"]
                    )

                await asyncio.sleep(2)

                node_found = None
                for node in self.client.nodes:
                    if node.name == identifier:
                        node_found = node
                        break

                if node_found and node_found.available:
                    print(f"[INFO LAVALINK]-> ✓ {identifier} connecté")
                    return True

            except Exception as error:
                logger.error(f"[ERROR LAVALINK]-> Connexion {identifier}: {error}", exc_info=True)
                print(f"[ERROR LAVALINK]-> Connexion {identifier}: {error}")

            if attempt < self.retry_attempts:
                await asyncio.sleep(2 ** attempt)

        return False

    def has_available_node(self) -> bool:
        """Vérifier qu'au moins 1 nœud est disponible"""
        if not self.client:
            return False
        return any(node.available for node in self.client.nodes)

    async def get_player(self, guild: discord.Guild):
        try:
            if not self.client:
                return None

            if not self.has_available_node():
                logger.warning("[WARNING LAVALINK]-> Aucun nœud lavalink disponible")
                print("[WARNING LAVALINK]-> Aucun nœud lavalink disponible")
                return None

            self.client.player_manager.create(guild.id)
            player = self.client.player_manager.get(guild.id)
            return player

        except Exception as error:
            logger.error(f"[ERROR LAVALINK]-> get_player {guild.id}: {error}", exc_info=True)
            print(f"[ERROR LAVALINK]-> get_player {guild.id}: {error}")
            return None

    async def disconnect_player(self, guild: discord.Guild) -> bool:
        try:
            if not self.client:
                return False

            player = self.client.player_manager.get(guild.id)
            if not player:
                return False

            player.queue.clear()
            await player.stop()

            voc_client= guild.voice_client
            if voc_client:
                try:
                    if hasattr(voc_client, 'is_connected'):
                        if callable(voc_client.is_connected):
                            if voc_client.is_connected():
                                await voc_client.disconnect(force=True)
                        else:
                            if voc_client.is_connected:
                                await voc_client.disconnect(force=True)
                    else:
                        await voc_client.disconnect(force=True)
                except Exception as error:
                    logger.warning(f"[WARNING LAVALINK]-> Erreur de déconnexion du player: {error}", exc_info=True)
                    print(f"[WARNING LAVALINK]-> Erreur de déconnexion du player: {error}")

            return True
        except Exception as error:
            logger.error(f"[ERROR LAVALINK]-> disconnect_player: {error}", exc_info=True)
            print(f"[ERROR LAVALINK]-> disconnect_player: {error}")
            return False

    @lavalink.listener(lavalink.TrackStartEvent)
    async def track_start(self, event: lavalink.TrackStartEvent):
        """Événement quand une piste commence à jouer"""
        print(f"[LAVALINK EVENT]-> Lecture musicale démarrée dans le serveur: {event.player.guild_id}: {event.track.title}")

    @lavalink.listener(lavalink.TrackEndEvent)
    async def track_end(self, event: lavalink.TrackEndEvent):
        """Événement quand une piste se termine"""
        print(f"[LAVALINK EVENT]-> Lecture musicale terminée dans le serveur: {event.player.guild_id}: {event.track.title}")
        if event.player.queue:
            await event.player.play()

    @lavalink.listener(lavalink.TrackExceptionEvent)
    async def track_exception(self, event: lavalink.TrackExceptionEvent):
        """Événement en cas d'erreur de lecture"""
        print(f"[LAVALINK EVENT]-> Lecture musicale échouée dans le serveur: {event.player.guild_id}: {event.exception}")

    @lavalink.listener(lavalink.QueueEndEvent)
    async def queue_finish(self, event: lavalink.QueueEndEvent):
        """Événement quand la queue est vide"""
        print(f"[LAVALINK EVENT]-> Queue de lecture musicale vide pour le serveur: {event.player.guild_id}")

    async def _healthcheck_loop(self):
        while True:
            try:
                await asyncio.sleep(self.healthcheck_interval)
                if not self.client:
                    continue

                unavailable_count = 0
                for node in self.client.nodes:
                    if not node.available:
                        unavailable_count += 1
                        logger.warning(f"[WARNING LAVALINK]-> Tentative reconnexion au node: {node.name}")
                        print(f"[WARNING LAVALINK]-> Tentative reconnexion au node: {node.name}")
                        for server in self.servers:
                            if server["identifier"] == node.name:
                                await self._connect_single_node(server)
                                break
                if unavailable_count == 0:
                    print("[INFO LAVALINK]-> Tous les nœuds sont opérationnels")

            except asyncio.CancelledError:
                break
            except Exception as error:
                logger.error(f"[ERROR LAVALINK]-> Healthcheck: {error}", exc_info=True)
                print(f"[ERROR LAVALINK]-> Healthcheck: {error}")

    def get_nodes_status(self) -> Dict[str, Any]:
        if not self.client:
            return {"total_nodes": 0, "nodes": []}

        nodes_info: List[Dict[str, Any]] = []

        for node in self.client.nodes:
            stats = node.stats

            # noinspection PyUnresolvedReferences
            nodes_info.append({
                "identifier": node.name,
                "available": node.available,
                "players": stats.players if stats else 0,
                "playing_players": stats.playing_players if stats else 0,
                "uptime": stats.uptime if stats else 0,
                "cpu_system_load": stats.cpu_system_load if stats else 0.0,
                "cpu_lavalink_load": stats.cpu_lavalink_load if stats else 0.0,
                "memory_used": stats.memory_used if stats else 0,
                "memory_free": stats.memory_free if stats else 0
            })

        return {
            "total_nodes": len(self.client.nodes),
            "connected_nodes": sum(1 for n in self.client.nodes if n.available),
            "nodes": nodes_info
        }

    async def reconnect_all_nodes(self) -> int:
        if not self.client:
            return 0

        reconnected = 0
        for server in self.servers:
            node_found = None
            for node in self.client.nodes:
                if node.name == server["identifier"]:
                    node_found = node
                    break

            if not node_found or not node_found.available:
                if await self._connect_single_node(server):
                    reconnected += 1

        return reconnected

    async def shutdown(self):
        try:
            if self.healthcheck_task and not self.healthcheck_task.done():
                self.healthcheck_task.cancel()
                try:
                    await self.healthcheck_task
                except asyncio.CancelledError:
                    pass

            if self.client:
                for node in self.client.nodes:
                    try:
                        await node.destroy()
                    except Exception as error:
                        logger.error(f"[ERROR LAVALINK]-> Shutdown {node.name}: {error}", exc_info=True)
                        print(f"[ERROR LAVALINK]-> Shutdown {node.name}: {error}")

            self.is_initialized = False

        except Exception as error:
            logger.error(f"[ERROR LAVALINK]-> Shutdown: {error}", exc_info=True)
            print(f"[ERROR LAVALINK]-> Shutdown: {error}")

    def __del__(self):
        if self.healthcheck_task and not self.healthcheck_task.done():
            self.healthcheck_task.cancel()