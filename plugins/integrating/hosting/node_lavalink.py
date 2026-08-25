"""Lavalink connection manager, voice protocol adapter, and healthcheck task."""

import asyncio
from typing import Optional, List, Dict, Any
import discord
import lavalink
from app.helps.utils import logger
from settings.config import params


class LavalinkVoiceClient(discord.VoiceProtocol):
    """Custom VoiceProtocol forwarding Discord voice events to Lavalink."""

    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        super().__init__(client, channel)
        self.client = client
        self.channel: Optional[discord.abc.Connectable] = channel
        self.guild_id = channel.guild.id
        self._destroyed = False

        if not hasattr(self.client, "lavalink"):
            self.client.lavalink = lavalink.Client(client.user.id)
        self.lavalink = self.client.lavalink

    def is_connected(self) -> bool:
        """Check connection state."""
        return self.channel is not None and not self._destroyed

    async def on_voice_server_update(self, data: dict):
        """Relay voice server updates."""
        lavalink_data = {"t": "VOICE_SERVER_UPDATE", "d": data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data: dict):
        """Relay voice state updates."""
        channel_id = data.get("channel_id")
        if not channel_id:
            await self._destroy()
            return

        self.channel = self.client.get_channel(int(channel_id))
        lavalink_data = {"t": "VOICE_STATE_UPDATE", "d": data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(
        self,
        *,
        timeout: float,
        reconnect: bool,
        self_deaf: bool = False,
        self_mute: bool = False,
    ) -> None:
        """Connect bot to voice channel."""
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def disconnect(self, *, force: bool = False) -> None:
        """Disconnect bot and clean up player state."""
        player = None
        if self.channel:
            player = self.lavalink.player_manager.get(self.channel.guild.id)

        if not force and (not player or not getattr(player, "is_connected", False)):
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
                logger.error(f"[ERROR LAVALINK] Error destroying player: {error}", exc_info=True)

    async def _destroy(self):
        if self._destroyed:
            return
        self._destroyed = True
        try:
            await self.lavalink.player_manager.destroy(self.guild_id)
        except Exception as error:
            logger.error(f"[ERROR LAVALINK] Error in _destroy: {error}", exc_info=True)


class LavalinkManager:
    """Manages Lavalink node pools, reconnection retries, and background healthchecks."""

    def __init__(
        self,
        connection_timeout: int = params.CONNEXION_TIMEOUT,
        retry_attempts: int = params.RETRY_ATTEMPTS,
        healthcheck_interval: int = params.HEALTHCHECK_INTERVAL,
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
        """Load configured Lavalink server host definitions."""
        configs: List[Dict[str, Any]] = []
        hosts = [(params.LAVALINK_HOST, "Server1")]

        for host, identifier in hosts:
            try:
                if not host or not host.strip():
                    logger.warning(f"[WARNING LAVALINK] {identifier} ignored (host not defined).")
                    continue

                configs.append(
                    {
                        "host": host.strip(),
                        "port": int(params.LAVALINK_PORT),
                        "password": params.LAVALINK_PASS,
                        "identifier": identifier,
                        "secure": False,
                    }
                )
            except (TypeError, ValueError) as error:
                logger.error(f"[ERROR LAVALINK] Configuration error for {identifier}: {error}", exc_info=True)

        return configs

    async def connect_nodes(self, bot: discord.Client) -> bool:
        """Connect all configured Lavalink nodes to client."""
        try:
            if not bot.is_ready():
                await bot.wait_until_ready()

            if not self.client:
                self.client = lavalink.Client(bot.user.id)
                self.client.add_event_hooks(self)
                bot.lavalink = self.client
                bot.add_listener(self.client.voice_update_handler, "on_socket_response")

            connected = 0
            for server in self.servers:
                if await self._connect_single_node(server):
                    connected += 1

            if connected == 0:
                logger.error("[ERROR LAVALINK] No Lavalink nodes connected successfully.")
                return False

            self.is_initialized = True

            if not self.healthcheck_task or self.healthcheck_task.done():
                self.healthcheck_task = asyncio.create_task(self._healthcheck_loop())
            return True

        except Exception as error:
            logger.error(f"[ERROR LAVALINK] Error during node connection: {error}", exc_info=True)
            return False

    async def _connect_single_node(self, server: Dict[str, Any]) -> bool:
        """Attempt to connect a single Lavalink node with exponential backoff."""
        identifier = server["identifier"]
        existing_node = None
        for node in self.client.nodes:
            if node.name == identifier:
                existing_node = node
                break

        if existing_node and existing_node.available:
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
                        ssl=server["secure"],
                    )

                await asyncio.sleep(2)

                node_found = None
                for node in self.client.nodes:
                    if node.name == identifier:
                        node_found = node
                        break

                if node_found and node_found.available:
                    print(f"[INFO LAVALINK] Connected to node: {identifier}")
                    return True

            except Exception as error:
                logger.error(f"[ERROR LAVALINK] Connection attempt {attempt} failed for {identifier}: {error}")

            if attempt < self.retry_attempts:
                await asyncio.sleep(2**attempt)

        return False

    def has_available_node(self) -> bool:
        """Verify that at least one Lavalink node is online and available."""
        if not self.client:
            return False
        return any(node.available for node in self.client.nodes)

    async def get_player(self, guild: discord.Guild):
        """Retrieve or create player instance for guild."""
        try:
            if not self.client or not self.has_available_node():
                return None

            self.client.player_manager.create(guild.id)
            return self.client.player_manager.get(guild.id)
        except Exception as error:
            logger.error(f"[ERROR LAVALINK] get_player error for guild {guild.id}: {error}", exc_info=True)
            return None

    async def disconnect_player(self, guild: discord.Guild) -> bool:
        """Stop player and disconnect voice client."""
        try:
            if not self.client:
                return False

            player = self.client.player_manager.get(guild.id)
            if not player:
                return False

            player.queue.clear()
            await player.stop()

            voc_client = guild.voice_client
            if voc_client:
                try:
                    if hasattr(voc_client, "is_connected") and callable(voc_client.is_connected):
                        if voc_client.is_connected():
                            await voc_client.disconnect(force=True)
                    else:
                        await voc_client.disconnect(force=True)
                except Exception as error:
                    logger.warning(f"[WARNING LAVALINK] Error disconnecting voice client: {error}", exc_info=True)

            return True
        except Exception as error:
            logger.error(f"[ERROR LAVALINK] disconnect_player error: {error}", exc_info=True)
            return False

    @lavalink.listener(lavalink.TrackStartEvent)
    async def track_start(self, event: lavalink.TrackStartEvent):
        """Handle track start event."""
        pass

    @lavalink.listener(lavalink.TrackEndEvent)
    async def track_end(self, event: lavalink.TrackEndEvent):
        """Handle track end event."""
        if event.player.queue:
            await event.player.play()

    @lavalink.listener(lavalink.TrackExceptionEvent)
    async def track_exception(self, event: lavalink.TrackExceptionEvent):
        """Handle track playback error."""
        logger.error(f"[LAVALINK EVENT] Track playback error in guild {event.player.guild_id}: {event.exception}")

    @lavalink.listener(lavalink.QueueEndEvent)
    async def queue_finish(self, event: lavalink.QueueEndEvent):
        """Handle empty queue event."""
        pass

    async def _healthcheck_loop(self):
        """Periodic background healthcheck for active Lavalink nodes."""
        while True:
            try:
                await asyncio.sleep(self.healthcheck_interval)
                if not self.client:
                    continue

                for node in self.client.nodes:
                    if not node.available:
                        logger.warning(f"[WARNING LAVALINK] Attempting reconnection to node: {node.name}")
                        for server in self.servers:
                            if server["identifier"] == node.name:
                                await self._connect_single_node(server)
                                break

            except asyncio.CancelledError:
                break
            except Exception as error:
                logger.error(f"[ERROR LAVALINK] Healthcheck error: {error}", exc_info=True)

    def get_nodes_status(self) -> Dict[str, Any]:
        """Return status metrics for all configured nodes."""
        if not self.client:
            return {"total_nodes": 0, "nodes": []}

        nodes_info: List[Dict[str, Any]] = []
        for node in self.client.nodes:
            stats = node.stats
            nodes_info.append(
                {
                    "identifier": node.name,
                    "available": node.available,
                    "players": stats.players if stats else 0,
                    "playing_players": stats.playing_players if stats else 0,
                    "uptime": stats.uptime if stats else 0,
                    "cpu_system_load": stats.cpu_system_load if stats else 0.0,
                    "cpu_lavalink_load": stats.cpu_lavalink_load if stats else 0.0,
                    "memory_used": stats.memory_used if stats else 0,
                    "memory_free": stats.memory_free if stats else 0,
                }
            )

        return {
            "total_nodes": len(self.client.nodes),
            "connected_nodes": sum(1 for n in self.client.nodes if n.available),
            "nodes": nodes_info,
        }

    async def reconnect_all_nodes(self) -> int:
        """Attempt to reconnect all disconnected nodes."""
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
        """Gracefully disconnect nodes and cancel background tasks."""
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
                        logger.error(f"[ERROR LAVALINK] Error shutting down node {node.name}: {error}", exc_info=True)

            self.is_initialized = False

        except Exception as error:
            logger.error(f"[ERROR LAVALINK] Shutdown error: {error}", exc_info=True)

    def __del__(self):
        if self.healthcheck_task and not self.healthcheck_task.done():
            self.healthcheck_task.cancel()