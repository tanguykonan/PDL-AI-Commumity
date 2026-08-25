"""Diagnostic, logging, and system monitoring slash commands for developers and administrators."""

import os
from typing import Dict, Any
from datetime import datetime
import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from app.helps.utils import logger, UsefulMethods
from settings.config import params
from plugins.integrating.hosting import node_vm
from plugins.integrating.storing.database import database


class Debug(commands.GroupCog, name="debug"):
    """Developer and diagnostic command group."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.monitor = node_vm.SystemMonitor(cache_duration=10, history_size=100)

    @staticmethod
    def _get_status_emoji(percentage: float) -> str:
        """Return a status emoji based on usage percentage."""
        if percentage < 50:
            return "🟢"
        if percentage < 75:
            return "🟡"
        if percentage < 90:
            return "🟠"
        return "🔴"

    @staticmethod
    def _get_status_color(cpu: float, ram: float, disk: float) -> discord.Color:
        """Determine embed color based on maximum hardware resource load."""
        max_usage = max(cpu, ram, disk)
        if max_usage < 50:
            return discord.Color.green()
        if max_usage < 75:
            return discord.Color.gold()
        if max_usage < 90:
            return discord.Color.orange()
        return discord.Color.red()

    @staticmethod
    def _format_uptime(seconds: float) -> str:
        """Format uptime seconds into a human-readable string."""
        try:
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            minutes = int((seconds % 3600) // 60)

            parts = []
            if days > 0:
                parts.append(f"{days}d")
            if hours > 0:
                parts.append(f"{hours}h")
            if minutes > 0:
                parts.append(f"{minutes}m")

            return " ".join(parts) if parts else "< 1m"
        except Exception as error:
            logger.error(f"[ERROR DEBUG] Failed to format uptime: {error}", exc_info=True)
            return "< 1m"

    def _create_basic_embed(self, info: Dict[str, Any]) -> discord.Embed:
        """Create a compact embed with core server load metrics."""
        cpu_usage = info["cpu"]["usage"]
        ram_usage = info["ram"]["usage"]
        disk_usage = info["disk"]["usage"]

        description = (
            f"```\n"
            f"{self._get_status_emoji(cpu_usage)} CPU:    {cpu_usage:>6.2f}%\n"
            f"{self._get_status_emoji(ram_usage)} RAM:    {ram_usage:>6.2f}%\n"
            f"{self._get_status_emoji(disk_usage)} Disk:   {disk_usage:>6.2f}%\n"
        )

        if info.get("gpu"):
            gpu_count = len(info["gpu"])
            avg_gpu_load = sum(g["load"] for g in info["gpu"]) / gpu_count
            description += f"{self._get_status_emoji(avg_gpu_load)} GPU:    {avg_gpu_load:>6.2f}% ({gpu_count} GPU{'s' if gpu_count > 1 else ''})\n"

        description += "```"
        embed = discord.Embed(
            title="System Monitoring",
            description=description,
            color=self._get_status_color(cpu_usage, ram_usage, disk_usage),
            timestamp=datetime.now(),
        )
        return embed

    def _create_detailed_embed(self, info: Dict[str, Any]) -> discord.Embed:
        """Create a detailed embed covering all hardware components."""
        cpu_usage = info["cpu"]["usage"]
        ram_usage = info["ram"]["usage"]
        disk_usage = info["disk"]["usage"]

        embed = discord.Embed(
            title="Detailed System Monitoring",
            color=self._get_status_color(cpu_usage, ram_usage, disk_usage),
            timestamp=datetime.now(),
        )

        cpu_info = info["cpu"]
        cpu_text = f"{self._get_status_emoji(cpu_usage)} **{cpu_usage:.2f}%**\n"
        if cpu_info.get("cores"):
            cpu_text += f"Cores: {cpu_info['cores']} physical, {cpu_info.get('threads', '?')} logical\n"
        if cpu_info.get("frequency") and cpu_info["frequency"]:
            freq = cpu_info["frequency"]
            cpu_text += f"Frequency: {freq['current']:.0f} MHz"
            if freq.get("max"):
                cpu_text += f" (max: {freq['max']:.0f} MHz)"
            cpu_text += "\n"
        if cpu_info.get("temperatures"):
            if len(cpu_info["temperatures"]) > 0:
                avg_temp = sum(cpu_info["temperatures"]) / len(cpu_info["temperatures"])
                cpu_text += f"Temperature: {avg_temp:.1f}°C"
            else:
                cpu_text += "Temperature: N/A"

        embed.add_field(name="CPU", value=cpu_text, inline=True)

        ram_info = info["ram"]
        ram_text = (
            f"{self._get_status_emoji(ram_usage)} **{ram_usage:.2f}%**\n"
            f"Used: {ram_info['used']}\n"
            f"Total: {ram_info['total']}\n"
            f"Available: {ram_info['available']}"
        )
        if ram_info.get("swap"):
            swap = ram_info["swap"]
            ram_text += f"\nSwap: {swap['usage']:.1f}% ({swap['used']}/{swap['total']})"

        embed.add_field(name="RAM", value=ram_text, inline=True)

        disk_info = info["disk"]
        disk_text = (
            f"{self._get_status_emoji(disk_usage)} **{disk_usage:.2f}%**\n"
            f"Used: {disk_info['used']}\n"
            f"Total: {disk_info['total']}\n"
            f"Free: {disk_info['free']}"
        )
        embed.add_field(name="Disk", value=disk_text, inline=True)

        if info.get("gpu"):
            for idx, gpu in enumerate(info["gpu"]):
                gpu_text = (
                    f"{self._get_status_emoji(gpu['load'])} **{gpu['load']:.2f}%**\n"
                    f"Model: {gpu.get('name', 'Unknown')}\n"
                    f"VRAM: {gpu['memoryUsed']}/{gpu['memoryTotal']} ({gpu['memoryPercent']:.1f}%)"
                )
                if gpu.get("temperature"):
                    gpu_text += f"\nTemp: {gpu['temperature']}°C"
                embed.add_field(name=f"GPU {idx}", value=gpu_text, inline=True)

        network_info = info["network"]
        network_text = f"Sent: {network_info['bytesSent']}\nReceived: {network_info['bytesReceived']}"
        if network_info.get("errorsIn", 0) > 0 or network_info.get("errorsOut", 0) > 0:
            network_text += f"\nErrors: {network_info['errorsIn']} in / {network_info['errorsOut']} out"
        embed.add_field(name="Network", value=network_text, inline=True)

        process_info = info["process"]
        process_text = (
            f"PID: {process_info['pid']}\n"
            f"CPU: {process_info['cpuPercent']:.2f}%\n"
            f"RAM: {process_info['memoryUsage']}\n"
            f"Threads: {process_info['threads']}"
        )
        embed.add_field(name="Bot Process", value=process_text, inline=True)

        platform_info = info["platform"]
        platform_text = (
            f"OS: {platform_info['system']} {platform_info['release']}\n"
            f"Arch: {platform_info['machine']}\n"
            f"Python: {platform_info['python']}\n"
            f"Uptime: {self._format_uptime(info['platform']['uptime'])}"
        )
        embed.add_field(name="System", value=platform_text, inline=True)
        embed.set_footer(text=f"Requested by {self.bot.user.name} • Refreshed every 10s")
        return embed

    @app_commands.command(name="observer", description="DEVS: Inspect recent error/warning logs.")
    @app_commands.describe(types="Type of debug log file", lines="Number of lines to read")
    @app_commands.choices(
        types=[
            Choice(name="error", value=params.ERROR_PATH),
            Choice(name="warning", value=params.WARNING_PATH),
        ]
    )
    async def observer(self, interaction: discord.Interaction, types: Choice[str], lines: int = 10):
        try:
            if not await UsefulMethods.check_is_guild(interaction):
                return await interaction.response.send_message("Commande indisponible en messages privés.", ephemeral=True)

            member = interaction.user
            has_permissions = database.is_admin(member.id) or UsefulMethods.check_is_support_member(member.id)

            if not has_permissions:
                logger.warning(f"[WARNING DEBUG] Unauthorized access attempt to logs by: {interaction.user.name}")
                return await interaction.response.send_message("Accès refusé. Vous n'avez pas les permissions nécessaires.", ephemeral=True)

            log_path = types.value
            if not os.path.exists(log_path):
                return await interaction.response.send_message(f"Fichier de log introuvable : {types.name}.", ephemeral=True)

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                lines_content = f.readlines()[-lines:]
            if not lines_content:
                return await interaction.response.send_message("Aucune entrée dans ce fichier de log.", ephemeral=True)

            msg = "".join(lines_content)[-1900:]
            embed = discord.Embed(
                title="Dernières erreurs du bot" if log_path == params.ERROR_PATH else "Derniers avertissements du bot",
                description=f"```{msg}```",
                color=discord.Color.red() if log_path == params.ERROR_PATH else discord.Color.yellow(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR DEBUG] Error reading logs: {error}", exc_info=True)
            return await interaction.response.send_message("Erreur lors de la lecture du fichier de log.", ephemeral=True)

    @app_commands.command(name="cleaning", description="DEVS: Clear a debug log file.")
    @app_commands.describe(file="Target log file to clear")
    @app_commands.choices(
        file=[
            Choice(name="error", value=params.ERROR_PATH),
            Choice(name="warning", value=params.WARNING_PATH),
        ]
    )
    async def cleaning(self, interaction: discord.Interaction, file: Choice[str]):
        try:
            if not await UsefulMethods.check_is_guild(interaction):
                return await interaction.response.send_message("Commande indisponible en messages privés.", ephemeral=True)

            member = interaction.user
            has_permissions = database.is_admin(member.id) or UsefulMethods.check_is_support_member(member.id)

            if not has_permissions:
                logger.warning(f"[WARNING DEBUG] Unauthorized log cleanup attempt by: {interaction.user.name}")
                return await interaction.response.send_message("Accès refusé.", ephemeral=True)

            files_to_clear = file.value
            if not os.path.exists(files_to_clear):
                return await interaction.response.send_message(f"Fichier {file.name} introuvable.", ephemeral=True)

            with open(files_to_clear, "w", encoding="utf-8"):
                pass
            return await interaction.response.send_message(f"Le fichier {file.name} a été nettoyé avec succès.", ephemeral=True)
        except Exception as error:
            logger.error(f"[ERROR DEBUG] Error clearing log: {error}", exc_info=True)
            return await interaction.response.send_message("Erreur lors du nettoyage du fichier.", ephemeral=True)

    @app_commands.command(name="hoster", description="DEVS: Display host system resource diagnostics.")
    @app_commands.describe(detailed="Display detailed metrics")
    async def hoster(self, interaction: discord.Interaction, detailed: bool = False):
        try:
            if not await UsefulMethods.check_is_guild(interaction):
                return await interaction.response.send_message("Commande indisponible en messages privés.", ephemeral=True)

            member = interaction.user
            has_permissions = database.is_admin(member.id) or UsefulMethods.check_is_support_member(member.id)

            if not has_permissions:
                logger.warning(f"[WARNING DEBUG] Unauthorized monitoring attempt by: {interaction.user.name}")
                return await interaction.response.send_message("Accès refusé.", ephemeral=True)

            await interaction.response.defer(ephemeral=True)
            info = self.monitor.get_hardware_info(use_cache=False)
            if not info:
                error_embed = discord.Embed(
                    title="Erreur de récupération",
                    description="Impossible de récupérer les informations système.",
                    color=discord.Color.red(),
                )
                return await interaction.followup.send(embed=error_embed)

            if detailed:
                embed = self._create_detailed_embed(info)
            else:
                embed = self._create_basic_embed(info)

            alerts = self.monitor.get_alerts()
            if alerts:
                alerts_text = "\n".join([f"{alert['message']}" for alert in alerts])
                embed.add_field(name="Alerts", value=alerts_text, inline=False)

            await interaction.followup.send(embed=embed)
        except Exception as error:
            logger.error(f"[ERROR DEBUG] Error fetching hoster info: {error}", exc_info=True)
            return await interaction.followup.send("Une erreur s'est produite lors de la récupération des données système.", ephemeral=True)

    @app_commands.command(name="alerts", description="DEVS: Display active system resource alerts.")
    async def alerts(self, interaction: discord.Interaction):
        try:
            if not await UsefulMethods.check_is_guild(interaction):
                return await interaction.response.send_message("Commande indisponible en messages privés.", ephemeral=True)

            member = interaction.user
            has_permissions = database.is_admin(member.id) or UsefulMethods.check_is_support_member(member.id)

            if not has_permissions:
                logger.warning(f"[WARNING DEBUG] Unauthorized alerts check by: {interaction.user.name}")
                return await interaction.response.send_message("Accès refusé.", ephemeral=True)

            alerts = self.monitor.get_alerts()
            if not alerts:
                embed = discord.Embed(
                    title="Aucune alerte",
                    description="Tous les systèmes fonctionnent normalement.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(),
                )
            else:
                embed = discord.Embed(
                    title="Alertes système",
                    description=f"{len(alerts)} alerte(s) active(s)",
                    color=discord.Color.red(),
                    timestamp=datetime.now(),
                )
                for alert in alerts:
                    level_emoji = "⚠️" if alert["level"] == "warning" else "🔴"
                    embed.add_field(name=f"{level_emoji} {alert['type'].upper()}", value=alert["message"], inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as error:
            logger.error(f"[ERROR DEBUG] Error displaying alerts: {error}", exc_info=True)
            return await interaction.response.send_message("Erreur lors de la récupération des alertes système.", ephemeral=True)

    @app_commands.command(name="reboot", description="DEVS: Gracefully close the bot process.")
    async def reboot(self, interaction: discord.Interaction):
        try:
            if not await UsefulMethods.check_is_guild(interaction):
                return await interaction.response.send_message("Commande indisponible en messages privés.", ephemeral=True)

            member = interaction.user
            has_permissions = database.is_admin(member.id) or UsefulMethods.check_is_support_member(member.id)

            if not has_permissions:
                logger.warning(f"[WARNING DEBUG] Unauthorized reboot attempt by: {interaction.user.name}")
                return await interaction.response.send_message("Accès refusé.", ephemeral=True)

            await interaction.response.send_message("Arrêt du bot en cours...", ephemeral=True)
            await self.bot.close()
        except Exception as error:
            logger.error(f"[ERROR DEBUG] Error during bot reboot: {error}", exc_info=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Debug(bot))