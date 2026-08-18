# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 30/12/2025
# ==================================================================================
import discord
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from app.helps.utils import logger
from settings.config import params
from plugins.integrating.storing.database import database

class Help(commands.GroupCog, name = "help"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name = "ping", description = "PUBLIC-> Consulter la latence du bot")
    async def ping(self, interaction: discord.Interaction):
        try:
            start_time = discord.utils.utcnow()
            end_time = discord.utils.utcnow()

            response_latency = round((end_time - start_time).total_seconds() * 1000)
            ws_latency = round(self.bot.latency * 1000)

            max_latency = max(response_latency, ws_latency)
            color = discord.Color.green() if max_latency < 100 else discord.Color.orange() if max_latency < 250 else discord.Color.red()

            embed = discord.Embed(
                description=(
                    f"<:ceanwingandswordids:1458915116266422532> **Latence de réponse:** `{response_latency}`ms.\n"
                    f"<:yellowwingandswordids:1458915216766140578> **Ping WebSocket:** `{ws_latency}`ms.\n"
                ),
                color=color
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)

        except Exception as error:
            logger.error(f"[ERROR HELP]-> Une erreur s'est produite lors de l'exécution de la commande ping : {error}", exc_info=True)
            await interaction.response.send_message(f"Mauvaise nouvelle l'ami. Cette commande bad.", ephemeral=True)

    @app_commands.command(name = 'infos', description = "PUBLIC-> Consulter les informations relatives au bot")
    async def infos(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                description = "**Voici quelques informations sur moi.**",
                color = 0x293133
            )
            statistics = database.get_stats()
            embed.set_author(name = self.bot.user.name, icon_url = self.bot.user.display_avatar.url)
            embed.add_field(name = '<:hypesquad:1298708390612172881> Version', value = f'`{params.VERSION}`', inline = False)
            embed.add_field(name='<:JinxFU:1367590304714199112> Date de création', value='`10 Octobre 2024`(J\'ai donc 1 an et + maintenant)')
            embed.add_field(name = '<:shinyredsparkles:1387880925760589976> Statistiques global', value = f'\n- Nombre d\'utilisateur: `{statistics["userNumber"]}` \n- Nombre de serveurs: `{statistics["serverNumber"]}`', inline = False)
            embed.add_field(name = '<a:emoji_7:1178303656425177158> Technologies utilisées', value = 'Je repose sur du `python`, un joli conteneur `docker` et quelques `services en Java` telles que Lavalink.')
            embed.add_field(name = "<:verifiedlightblue:1387880989715599410> Équipe PDL-AI", value = "La team support de **PDL-AI** est composée de `quatre (4)` principaux acteurs avec : \n- `@nythique` pour le développement; \n- `@tintin3` pour la surveillance de la consommation des ressources, et la validation des ajouts; \n- `@paxiz_` pour la puissance matérielle de ses serveurs et ses conseils. \n- `@1flexible` pour le contrôle du noyau des intégrations.", inline=False)
            embed.add_field(name = '<:bughunterlvl2:1298708783845085236> Contributions', value = f"\n- `Développement`: Si vous le souhaitez tout en étant animé par de bonnes intentions, vous pouvez rejoindre la team du support en tant que développeur ou développeuse ; \n- `Dons`: Et oui, vous pouvez même sans connaissance en informatique, contribuer à ce projet qui vous tient à cœur.", inline = False)

            invite_url = f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=8"

            view = discord.ui.View()
            bouton_website = discord.ui.Button(
                label="Visiter le site",
                url="https://ai.pcpdl.eu/",
                style=discord.ButtonStyle.link
            )
            bouton_invite = discord.ui.Button(
                label="Inviter pdl.ai",
                url=invite_url,
                style=discord.ButtonStyle.link
            )
            bouton_donate = discord.ui.Button(
                label="Soutenir",
                url="https://ko-fi.com/pdlai44",
                style=discord.ButtonStyle.link
            )
            bouton_support = discord.ui.Button(
                label="Support",
                url="https://discord.gg/pc-pays-de-la-loire-1072925050409324644",
                style=discord.ButtonStyle.link
            )
            view.add_item(bouton_website)
            view.add_item(bouton_invite)
            view.add_item(bouton_donate)
            view.add_item(bouton_support)


            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

        except Exception as error:
            logger.error(f"[ERROR HELP]=> Une erreur s'est produite lors de l'affichage des informations du bot: {error}", exc_info=True)
            print(f"[ERROR HELP]=> Une erreur s'est produite lors de l'affichage des informations du bot: {error}")
            await interaction.response.send_message(f"Oups. Tu sais quoi, je pense que tu devrais signaler un bug à ce niveau.", ephemeral=True)

    @app_commands.command(name='commands', description="PUBLIC-> Consulter la liste des commandes du bot")
    async def commands(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                description="**Voici mes principales commandes et fonctionnalités.**",
                color=0x293133
            )
            embed.set_author(name = self.bot.user.name, icon_url = self.bot.user.display_avatar.url)
            embed.add_field(name = "<:pepecry:1387880873449226280> /help", value = "Consulter les aides liées à mon utilisation: \n- `/help ping`: Voire ma latence en ms. \n- `/help infos`: Voire les informations sur moi. \n- `/help commands`: Voire le menu d'aide pour les fonctionnalités. \n- `/help support`: Envoyer un signalement ou une suggestion au support.", inline=False)
            embed.add_field(name = "<:shinyredmoderator:1387880917045084262> /staff", value = "Définir les règles à appliquer sur ce serveur: \n- `/staff config` -> Accéder au panel de configuration du bot. \n- `/staff punish`: Appliquer des sanctions à un membre du serveur. \n- `/staff contest`: Supprimer des sanctions appliquées à un membre. \n- `/staff clear`: Supprimer des message sur le serveur.", inline=False)
            embed.add_field(name = "<a:monkeymid:1369996618916692038> /music", value = "Controller votre partie d'écoute: \n- `/music play`: Jouer une musique (nom ou URL). \n- `/music stop`: Arrêter la musique et déconnecter le bot. \n- `/music pause`: Mettre en pause la musique en cours. \n- `/music resume`: Reprendre la lecture de la musique. \n- `/music skip`: Passer à la musique suivante. \n- `/music queue`: Afficher la file d'attente des musiques. \n- `/music nowplaying`: Voir la musique actuellement en lecture. \n- `/music volume`: Ajuster le volume (0-100).", inline=False)
            embed.add_field(name = "🤖 Intelligence Artificielle (Neuro)", value = "Discutez avec moi naturellement ! Je suis un assistant intelligent capable de : \n- 🌐 **Recherches Web** : Actualités, météo, informations récentes. \n- 🎵 **Gestion Musicale** : Demandez-moi de mettre de la musique. \n- 📊 **Analyse Serveur** : Obtenir les statistiques et rôles. \n- 🧠 **Mémoire (RAG)** : Retenir le contexte de la communauté.", inline=False)
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

            invite_url = f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=8"

            view = discord.ui.View()
            bouton_invite = discord.ui.Button(
                label="Inviter pdl.ai",
                url=invite_url,
                style=discord.ButtonStyle.link
            )
            bouton_support = discord.ui.Button(
                label="Support",
                url="https://discord.gg/pc-pays-de-la-loire-1072925050409324644",
                style=discord.ButtonStyle.link
            )
            view.add_item(bouton_invite)
            view.add_item(bouton_support)

            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

        except Exception as e:
            logger.error(f"[ERROR HELP]-> Erreur lors de l'affichage de l'aide pour {interaction.user} ({interaction.user.id}): {e}",exc_info=True)
            await interaction.response.send_message(f"Désolé un bug peu courant s'est produit. Contact directement le support si le problème persiste.", ephemeral=True)

    @app_commands.command(name='support', description='PUBLIC-> Soumettre un report ou une suggestion au support')
    @app_commands.describe(message="Décris ton problème ou ta suggestion")
    async def support(self, interaction: discord.Interaction, message: str):
        try:
            await interaction.response.defer(ephemeral=True)
            if len(message.strip()) > 4000:
                await interaction.followup.send(f"Désolé mais ton message est beaucoup trop long pour être soumis via cette commande. Contact le support directement.", ephemeral=True)

            report_embed = discord.Embed(
                title=f"<:pepeangryping:1387880861642391694> Formulaire de {interaction.user.display_name}",
                description=f"```{message}```",
                color=0x293133,
                timestamp=datetime.now()
            )
            report_embed.set_author(name = interaction.user.display_name, icon_url = interaction.user.display_avatar.url)
            report_embed.set_footer(text = f"Identifiant de {interaction.user.display_name}: {interaction.user.id}")
            channel_id = int(params.SUPPORT_CHANNEL)
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(embed=report_embed)
                await interaction.followup.send(f"J'ai bien envoyé ton message au support. Merci pour ton retour !", ephemeral=True)
            else:
                support_ids = [int(x.strip()) for x in params.SUPPORT_MEMBERS.strip("()").split(",") if x.strip()]
                if support_ids:
                    admin = await self.bot.fetch_user(support_ids[0])
                    await admin.send(embed=report_embed)
                await interaction.followup.send(f"J'ai bien envoyé ton message au support. Merci pour ton retour !", ephemeral=True)

        except Exception as e:
            logger.error(f"[HELP ERROR]-> Une erreur lors de l'envoi du rapport par {interaction.user} ({interaction.user.id}) s'est produite: {e}", exc_info=True)
            await interaction.followup.send(f"Désolé mais votre requête a échouée. Si le problème persiste, contact directement le support.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))