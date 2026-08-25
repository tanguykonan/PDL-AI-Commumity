"""Help, latency, diagnostics, and support slash commands for users."""

from datetime import datetime
import discord
from discord.ext import commands
from discord import app_commands
from app.helps.utils import logger
from settings.config import params
from plugins.integrating.storing.database import database


class Help(commands.GroupCog, name="help"):
    """Public help and support command group."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="PUBLIC: Check bot and WebSocket latency.")
    async def ping(self, interaction: discord.Interaction):
        try:
            start_time = discord.utils.utcnow()
            end_time = discord.utils.utcnow()

            response_latency = round((end_time - start_time).total_seconds() * 1000)
            ws_latency = round(self.bot.latency * 1000)

            max_latency = max(response_latency, ws_latency)
            color = (
                discord.Color.green()
                if max_latency < 100
                else discord.Color.orange()
                if max_latency < 250
                else discord.Color.red()
            )

            embed = discord.Embed(
                description=(
                    f"📡 **Latence de réponse :** `{response_latency}`ms\n"
                    f"⚡ **Ping WebSocket :** `{ws_latency}`ms\n"
                ),
                color=color,
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)

        except Exception as error:
            logger.error(f"[ERROR HELP] Error in ping command: {error}", exc_info=True)
            await interaction.response.send_message("Une erreur s'est produite lors de la mesure du ping.", ephemeral=True)

    @app_commands.command(name="infos", description="PUBLIC: Display bot version, metrics, and information.")
    async def infos(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                description="**Voici les informations relatives à PDL-AI.**",
                color=0x293133,
            )
            statistics = database.get_stats()
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url)
            embed.add_field(name="📌 Version", value=f"`{params.VERSION}`", inline=False)
            embed.add_field(
                name="📊 Statistiques globales",
                value=f"- Utilisateurs: `{statistics['userNumber']}`\n- Serveurs: `{statistics['serverNumber']}`",
                inline=False,
            )
            embed.add_field(
                name="⚙️ Technologies",
                value="Développé en `Python 3.11` avec `discord.py`, `Groq API`, `ChromaDB` et `Lavalink v4`.",
                inline=False,
            )
            embed.add_field(
                name="👥 Édition Communautaire",
                value="Projet open-source sous licence **MIT**. N'hésitez pas à contribuer ou à personnaliser vos prompts et tutoriels.",
                inline=False,
            )

            invite_url = f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=8"

            view = discord.ui.View()
            btn_invite = discord.ui.Button(
                label="Inviter le bot",
                url=invite_url,
                style=discord.ButtonStyle.link,
            )
            view.add_item(btn_invite)

            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

        except Exception as error:
            logger.error(f"[ERROR HELP] Error displaying bot info: {error}", exc_info=True)
            await interaction.response.send_message("Erreur lors de l'affichage des informations.", ephemeral=True)

    @app_commands.command(name="commands", description="PUBLIC: Display list of bot commands and capabilities.")
    async def commands(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                description="**Voici les principales commandes et fonctionnalités disponibles.**",
                color=0x293133,
            )
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url)
            embed.add_field(
                name="ℹ️ /help",
                value=(
                    "- `/help ping` : Vérifier la latence du bot.\n"
                    "- `/help infos` : Afficher les statistiques et informations.\n"
                    "- `/help commands` : Afficher la liste des commandes.\n"
                    "- `/help support` : Soumettre un message au support."
                ),
                inline=False,
            )
            embed.add_field(
                name="🛡️ /staff",
                value=(
                    "- `/staff config` : Ouvrir le panneau de configuration interactif.\n"
                    "- `/staff punish` : Appliquer une sanction (timeout/ban).\n"
                    "- `/staff contest` : Révoquer une sanction.\n"
                    "- `/staff clear` : Supprimer des messages récents."
                ),
                inline=False,
            )
            embed.add_field(
                name="🎵 /music",
                value=(
                    "- `/music play <titre/url>` : Jouer une musique.\n"
                    "- `/music pause` / `/music resume` : Mettre en pause ou reprendre.\n"
                    "- `/music skip` : Passer à la piste suivante.\n"
                    "- `/music stop` : Arrêter la musique et déconnecter.\n"
                    "- `/music queue` : Voir la file d'attente.\n"
                    "- `/music volume <1-100>` : Régler le volume."
                ),
                inline=False,
            )
            embed.add_field(
                name="🤖 Intelligence Artificielle & Outils",
                value=(
                    "Mentionnez le bot pour discuter naturellement :\n"
                    "- 🌐 **Recherche Web** : Réponses enrichies avec les données internet récentes.\n"
                    "- 📚 **RAG & Base de Connaissances** : Indexation locale des tutoriels du serveur.\n"
                    "- 🧠 **Mémoire DDR** : Profils et suivi continu des conversations."
                ),
                inline=False,
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

            invite_url = f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=8"
            view = discord.ui.View()
            btn_invite = discord.ui.Button(label="Inviter le bot", url=invite_url, style=discord.ButtonStyle.link)
            view.add_item(btn_invite)

            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

        except Exception as e:
            logger.error(f"[ERROR HELP] Error in help commands: {e}", exc_info=True)
            await interaction.response.send_message("Une erreur s'est produite lors de l'affichage de l'aide.", ephemeral=True)

    @app_commands.command(name="support", description="PUBLIC: Submit a report or suggestion to the administrators.")
    @app_commands.describe(message="Describe your issue or suggestion")
    async def support(self, interaction: discord.Interaction, message: str):
        try:
            await interaction.response.defer(ephemeral=True)
            if len(message.strip()) > 4000:
                return await interaction.followup.send(
                    "Votre message est trop long (maximum 4000 caractères).", ephemeral=True
                )

            report_embed = discord.Embed(
                title=f"📩 Message Support de {interaction.user.display_name}",
                description=f"```{message}```",
                color=0x293133,
                timestamp=datetime.now(),
            )
            report_embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            report_embed.set_footer(text=f"User ID: {interaction.user.id}")

            channel_id = int(params.SUPPORT_CHANNEL) if params.SUPPORT_CHANNEL else None
            sent = False

            if channel_id:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(embed=report_embed)
                    sent = True

            if not sent and params.SUPPORT_MEMBERS:
                support_ids = [int(x.strip()) for x in params.SUPPORT_MEMBERS.strip("()").split(",") if x.strip()]
                if support_ids:
                    admin = await self.bot.fetch_user(support_ids[0])
                    if admin:
                        await admin.send(embed=report_embed)
                        sent = True

            await interaction.followup.send("Votre message a bien été transmis au support. Merci !", ephemeral=True)

        except Exception as e:
            logger.error(f"[HELP ERROR] Error sending support message: {e}", exc_info=True)
            await interaction.followup.send("Échec de l'envoi de votre message au support.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))