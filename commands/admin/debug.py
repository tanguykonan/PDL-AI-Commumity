# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 30/12/2025
# ==================================================================================
import  os
import discord
from typing import Dict, Any
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from app.helps.utils import logger
from settings.config import params
from discord.app_commands import Choice
from app.helps.utils import UsefulMethods
from plugins.integrating.hosting import node_vm
from plugins.integrating.storing.database import database

class Debug(commands.GroupCog, name = "debug"):
    def __init__(self, bot):
        self.bot = bot
        self.monitor = node_vm.SystemMonitor(cache_duration=10, history_size=100)

    @staticmethod
    def _get_status_emoji(percentage: float) -> str:
        """Retourner un emoji basé sur le pourcentage d'utilisation du serveur"""
        if percentage < 50:
            return "🟢"
        elif percentage < 75:
            return "🟡"
        elif percentage < 90:
            return "🟠"
        else:
            return "🔴"

    @staticmethod
    def _get_status_color(cpu: float, ram: float, disk: float) -> discord.Color:
        """Déterminer la couleur de l'embed selon l'état du serveur"""
        max_usage = max(cpu, ram, disk)
        if max_usage < 50:
            return discord.Color.green()
        elif max_usage < 75:
            return discord.Color.gold()
        elif max_usage < 90:
            return discord.Color.orange()
        else:
            return discord.Color.red()

    @staticmethod
    def _format_uptime(seconds: float) -> str:
        """Formater le temps au format lisible"""
        try:
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            minutes = int((seconds % 3600) // 60)

            parts = []
            if days > 0:
                parts.append(f"{days}j")
            if hours > 0:
                parts.append(f"{hours}h")
            if minutes > 0:
                parts.append(f"{minutes}m")

            return " ".join(parts) if parts else "< 1m"
        except Exception as error:
            logger.error(f"[ERROR DEBUG]=> Une erreur s'est produite lors du formatage du temps {error}")
            print(f"[ERROR DEBUG]=> Une erreur s'est produite lors du formatage du temps {error}")
            return f"< 1m"

    def _create_basic_embed(self, info: Dict[str, Any]) -> discord.Embed:
        """Créer un embed basique avec les informations principales du serveur"""
        cpu_usage = info['cpu']['usage']
        ram_usage = info['ram']['usage']
        disk_usage = info['disk']['usage']

        description = (
            f"```\n"
            f"{self._get_status_emoji(cpu_usage)} CPU:    {cpu_usage:>6.2f}%\n"
            f"{self._get_status_emoji(ram_usage)} RAM:    {ram_usage:>6.2f}%\n"
            f"{self._get_status_emoji(disk_usage)} Disque: {disk_usage:>6.2f}%\n"
        )

        if info.get('gpu'):
            gpu_count = len(info['gpu'])
            avg_gpu_load = sum(g['load'] for g in info['gpu']) / gpu_count
            description += f"{self._get_status_emoji(avg_gpu_load)} GPU:    {avg_gpu_load:>6.2f}% ({gpu_count} GPU{'s' if gpu_count > 1 else ''})\n"

        description += "```"
        embed = discord.Embed(
            title="Monitoring Système",
            description=description,
            color=self._get_status_color(cpu_usage, ram_usage, disk_usage),
            timestamp=datetime.now()
        )
        return embed

    def _create_detailed_embed(self, info: Dict[str, Any]) -> discord.Embed:
        """Créer un embed détaillé avec toutes les informations du serveur"""
        cpu_usage = info['cpu']['usage']
        ram_usage = info['ram']['usage']
        disk_usage = info['disk']['usage']

        embed = discord.Embed(
            title="Monitoring Système Détaillé",
            color=self._get_status_color(cpu_usage, ram_usage, disk_usage),
            timestamp=datetime.now()
        )

        cpu_info = info['cpu']
        cpu_text = f"{self._get_status_emoji(cpu_usage)} **{cpu_usage:.2f}%**\n"
        if cpu_info.get('cores'):
            cpu_text += f"Cœurs: {cpu_info['cores']} physiques, {cpu_info.get('threads', '?')} logiques\n"
        if cpu_info.get('frequency') and cpu_info['frequency']:
            freq = cpu_info['frequency']
            cpu_text += f"Fréquence: {freq['current']:.0f} MHz"
            if freq.get('max'):
                cpu_text += f" (max: {freq['max']:.0f} MHz)"
            cpu_text += "\n"
        if cpu_info.get('temperatures'):
            if len(cpu_info['temperatures']) > 0:
                avg_temp = sum(cpu_info['temperatures']) / len(cpu_info['temperatures']) #type:ignore
                cpu_text += f"Température: {avg_temp:.1f}°C"
            else:
                cpu_text += "Température: N/A"

        embed.add_field(name="CPU", value=cpu_text, inline=True)

        ram_info = info['ram']
        ram_text = (
            f"{self._get_status_emoji(ram_usage)} **{ram_usage:.2f}%**\n"
            f"Utilisé: {ram_info['used']}\n"
            f"Total: {ram_info['total']}\n"
            f"Disponible: {ram_info['available']}"
        )
        if ram_info.get('swap'):
            swap = ram_info['swap']
            ram_text += f"\nSwap: {swap['usage']:.1f}% ({swap['used']}/{swap['total']})"

        embed.add_field(name="RAM", value=ram_text, inline=True)

        disk_info = info['disk']
        disk_text = (
            f"{self._get_status_emoji(disk_usage)} **{disk_usage:.2f}%**\n"
            f"Utilisé: {disk_info['used']}\n"
            f"Total: {disk_info['total']}\n"
            f"Libre: {disk_info['free']}"
        )

        embed.add_field(name="Disque", value=disk_text, inline=True)

        if info.get('gpu'):
            for idx, gpu in enumerate(info['gpu']):
                gpu_text = (
                    f"{self._get_status_emoji(gpu['load'])} **{gpu['load']:.2f}%**\n"
                    f"Modèle: {gpu.get('name', 'Inconnu')}\n"
                    f"VRAM: {gpu['memoryUsed']}/{gpu['memoryTotal']} ({gpu['memoryPercent']:.1f}%)"
                )
                if gpu.get('temperature'):
                    gpu_text += f"\nTemp: {gpu['temperature']}°C"

                embed.add_field(
                    name=f"GPU {idx}",
                    value=gpu_text,
                    inline=True
                )

        network_info = info['network']
        network_text = (
            f"Envoyé: {network_info['bytesSent']}\n"
            f"Reçu: {network_info['bytesReceived']}"
        )
        if network_info.get('errorsIn', 0) > 0 or network_info.get('errorsOut', 0) > 0:
            network_text += f"\nErreurs: {network_info['errorsIn']} in / {network_info['errorsOut']} out"

        embed.add_field(name="Réseau", value=network_text, inline=True)

        process_info = info['process']
        process_text = (
            f"PID: {process_info['pid']}\n"
            f"CPU: {process_info['cpuPercent']:.2f}%\n"
            f"RAM: {process_info['memoryUsage']}\n"
            f"Threads: {process_info['threads']}"
        )

        embed.add_field(name="Processus Bot", value=process_text, inline=True)

        platform_info = info['platform']
        platform_text = (
            f"OS: {platform_info['system']} {platform_info['release']}\n"
            f"Machine: {platform_info['machine']}\n"
            f"Python: {platform_info['python']}\n"
            f"Uptime: {self._format_uptime(info['platform']['uptime'])}"
        )

        embed.add_field(name="Système", value=platform_text, inline=True)
        embed.set_footer(text=f"Demandé par {self.bot.user.name} • Mise à jour toutes les 10s")

        return embed

    @app_commands.command(name = "observer", description = "DEVS-> Observer les derniers bugs identifiés")
    @app_commands.describe(types = "Type d'informations de débogage", lines = "Nombre de lignes à lignes de logs")
    @app_commands.choices(types =[
        Choice(name = 'error', value = params.ERROR_PATH),
        Choice(name = 'warning', value = params.WARNING_PATH)
    ])
    async def observer(self, interaction: discord.Interaction, types: Choice[str], lines: int = 10):
        try:
            if not await UsefulMethods.check_is_guild(interaction):
                return await interaction.response.send_message("Tu te fou de ma gueule c'est ca !? Et bien va e faire foutre.")

            member = interaction.user
            has_permissions = (
                database.is_admin(member.id) or
                UsefulMethods.check_is_support_member(member.id)
            )

            if not has_permissions:
                logger.warning(f"[WARNING DEBUG] Utilisateur non autorisé a tenté d'accéder aux erreurs : {interaction.user.name}")
                print(f"[WARNING DEBUG] Utilisateur non autorisé a tenté d'accéder aux erreurs : {interaction.user.name}")
                return await interaction.response.send_message("Mais putain, tu fou quoi toi ? T'en as pas le droit tu m'entent !?", ephemeral=True)

            log_path = types.value
            if not os.path.exists(log_path):
                return await interaction.response.send_message(f"Je crois qu'il y a de la merde sur moi. Je ne trouve pas le fichier {types.name}.", ephemeral=True)

            with open(log_path, "r", encoding="utf-8", errors='replace') as f:
                lines_content = f.readlines()[-lines:]
            if not lines_content:
                return await interaction.response.send_message("Je suis saint moi.", ephemeral=True)

            msg = "".join(lines_content)[-1900:]
            embed = discord.Embed(
                title = "Dernières erreurs du bot" if log_path == params.ERROR_PATH else "Dernières avertissements du bot",
                description = f"```{msg}```",
                color   =  discord.Color.red() if log_path == params.ERROR_PATH else discord.Color.yellow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as error:
            logger.error(f"[ERROR DEBUG] Erreur lors de la lecture des debug : {error}")
            print(f"[ERROR DEBUG] Erreur lors de la lecture des debug : {error}")
            return await interaction.response.send_message("Je crois qu'il y a de la merde sur moi. Je n'arrive pas à lire ce putain de fichier de debug.", ephemeral=True)


    @app_commands.command(name = "cleaning", description = "DEVS-> Nettoyer un fichier de débogage")
    @app_commands.describe(file = "Fichier visé par le nettoyage")
    @app_commands.choices(file =[
        Choice(name = 'error', value = params.ERROR_PATH),
        Choice(name = 'warning', value = params.WARNING_PATH)
    ])
    async def cleaning(self, interaction: discord.Interaction, file: Choice[str]):
        try:
            if not await UsefulMethods.check_is_guild(interaction):
                return await interaction.response.send_message("Tu te fou de ma gueule c'est ca !? Et bien va e faire foutre.")

            member = interaction.user
            has_permissions = (
                database.is_admin(member.id) or
                UsefulMethods.check_is_support_member(member.id)
            )

            if not has_permissions:
                logger.warning(f"[WARNING DEBUG] Utilisateur non autorisé a tenté de nettoyer un fichier de débogage : {interaction.user.name}")
                print(f"[WARNING DEBUG] Utilisateur non autorisé a tenté de nettoyer un fichier de débogage : {interaction.user.name}")
                return await interaction.response.send_message("Mais putain, tu fou quoi toi ? T'en as pas le droit tu m'entent !?", ephemeral=True)

            files_to_clear = file.value
            if not os.path.exists(files_to_clear):
                return await interaction.response.send_message(f"Je crois qu'il y a de la merde sur moi. Je ne trouve pas le fichier {file.name}.", ephemeral=True)

            with open(files_to_clear, "w", encoding="utf-8"):
                pass
            return await interaction.response.send_message(f"Bravo {interaction.user.name}, tu viens d'éffacer tous mes espoirs.", ephemeral=True)
        except Exception as error:
            logger.error(f"[ERROR DEBUG]=> Une erreur lors du nettoyage des debug : {error}")
            print(f"[ERROR DEBUG]=> Une erreur lors du nettoyage des debug : {error}")

    @app_commands.command(name = "hoster", description = "DEVS-> Afficher les informations de monitoring de l'hôte du bot")
    @app_commands.describe(detailed = "Afficher les informations détaillées")
    async def hoster(self, interaction: discord.Interaction, detailed: bool = False):
        try:
            if not await UsefulMethods.check_is_guild(interaction):
                return await interaction.response.send_message("Tu te fou de ma gueule c'est ca !? Et bien va e faire foutre.")

            member = interaction.user
            has_permissions = (
                    database.is_admin(member.id) or
                    UsefulMethods.check_is_support_member(member.id)
            )

            if not has_permissions:
                logger.warning(f"[WARNING DEBUG] Utilisateur non autorisé a tenté d'accéder informations de monitoring sur l'hôte du bot : {interaction.user.name}")
                print(f"[WARNING DEBUG] Utilisateur non autorisé a tenté d'accéder informations de monitoring sur l'hôte du bot : {interaction.user.name}")
                return await interaction.response.send_message("Mais putain, tu fou quoi toi ? T'en as pas le droit tu m'entent !?", ephemeral=True)

            await interaction.response.defer(ephemeral=True)
            info = self.monitor.get_hardware_info(use_cache=False)
            if not info:
                error_embed = discord.Embed(
                    title="Erreur de récupération",
                        description="Impossible de récupérer les informations système.",
                        color=discord.Color.red()
                )
                logger.error("[ERROR DEBUG]-> Échec de récupération des infos système")
                print("[ERROR DEBUG]-> Échec de récupération des infos système")
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
            logger.error(f"[ERROR DEBUG]=> Une erreur s'est produite lors de l'affichage des informations de monitoring : {error}")
            print(f"[ERROR DEBUG]=> Une erreur s'est produite lors de l'affichage des informations de monitoring : {error}")
            return await interaction.followup.send(f"Eh merde. Une erreur s'est produite lors de la récupération des données. Je ne capte plus rien.", ephemeral=True)

    @app_commands.command(name="alerts", description="DEVS-> Afficher les alertes système en cours")
    async def alerts(self, interaction: discord.Interaction):
        try:
            if not await UsefulMethods.check_is_guild(interaction):
                return await interaction.response.send_message("Tu te fou de ma gueule c'est ca !? Et bien va e faire foutre.")

            member = interaction.user
            has_permissions = (
                    database.is_admin(member.id) or
                    UsefulMethods.check_is_support_member(member.id)
            )

            if not has_permissions:
                logger.warning(f"[WARNING DEBUG] Utilisateur non autorisé a tenté d'accéder aux alertes système en cours : {interaction.user.name}")
                print(f"[WARNING DEBUG] Utilisateur non autorisé a tenté d'accéder aux alertes système en cours : {interaction.user.name}")
                return await interaction.response.send_message("Mais putain, tu fou quoi toi ? T'en as pas le droit tu m'entent !?", ephemeral=True)

            alerts = self.monitor.get_alerts()
            if not alerts:
                embed = discord.Embed(
                    title="Aucune alerte",
                    description="Tous les systèmes fonctionnent normalement.",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
            else:
                embed = discord.Embed(
                    title="Alertes système",
                    description=f"{len(alerts)} alerte(s) active(s)",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )

                for alert in alerts:
                    level_emoji = "⚠️" if alert['level'] == 'warning' else "🔴"
                    embed.add_field(
                        name=f"{level_emoji} {alert['type'].upper()}",
                        value=alert['message'],
                        inline=False
                    )

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as error:
            logger.error(f"[ERROR DEBUG]=> Une erreur s'est produite lors de l'affichage des alertes système en cours {error}")
            print(f"[ERROR DEBUG]=> Une erreur s'est produite lors de l'affichage des alertes système en cours {error}")
            return await interaction.response.send_message('Non, non, ne me dis pas que tu as merdé même pour cette commande.', ephemeral=True)

    @app_commands.command(name="reboot", description="DEVS-> Redémarrer rapidement le bot")
    async def reboot(self, interaction: discord.Interaction):
        try:
            if not await UsefulMethods.check_is_guild(interaction):
                return await interaction.response.send_message("Tu te fou de ma gueule c'est ca !? Et bien va e faire foutre.")

            member = interaction.user
            has_permissions = (
                    database.is_admin(member.id) or
                    UsefulMethods.check_is_support_member(member.id)
            )

            if not has_permissions:
                logger.warning(f"[WARNING DEBUG] Utilisateur non autorisé a tenté de redémarrer le bot : {interaction.user.name}")
                print(f"[WARNING DEBUG] Utilisateur non autorisé a tenté de redémarrer le bot : {interaction.user.name}")
                return await interaction.response.send_message("Mais putain, tu fou quoi toi ? T'en as pas le droit tu m'entent !?", ephemeral=True)

            client = self.bot
            await interaction.response.send_message('C\'est chiant de devoir redémarrer encore.', ephemeral=True)
            await client.close()
        except Exception as error:
            logger.error(f"[ERROR DEBUG]=> Une erreur s'est produite lors de l'affichage des alertes système en cours {error}")
            print(f"[ERROR DEBUG]=> Une erreur s'est produite lors de l'affichage des alertes système en cours {error}")

async def setup(bot):
    await bot.add_cog(Debug(bot))