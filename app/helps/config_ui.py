# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 22/04/2026
# ==================================================================================
import discord
import datetime
from app.helps.utils import logger
from plugins.integrating.storing.database import database


# ==================================================================================
# ================================ HELPERS EMBED ===================================
# ==================================================================================

# ── Helper des embeds ─────────────────────────────────────────
def _base_embed(interaction: discord.Interaction, title: str) -> discord.Embed:

    embed = discord.Embed(title=title, color=discord.Color.red())

    if interaction.guild and interaction.guild.icon: #type:ignore
        embed.set_author(name="Configuration du serveur", icon_url=interaction.guild.icon.url) #type:ignore
        embed.set_thumbnail(url=interaction.guild.icon.url) #type:ignore

    embed.set_footer(
        text=f"Demandé par @{interaction.user.name}",
        icon_url=interaction.user.display_avatar.url,
    )
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    return embed


# ── Embed d'accueil ─────────────────────────────────────────
def build_accueil_embed_page(interaction: discord.Interaction) -> discord.Embed:

    embed = _base_embed(interaction, "__Page d'accueil__")
    embed.add_field(name=":gear: • **Configuration générale**", value="Configuration du système d'interaction global: La langue, le mode, les salons de discussions.", inline=False)
    embed.add_field(name=":shield: • **Analyse de sécurité**", value="Configuration de l'analyse automatique des liens et médias : détection des contenus dangereux ou suspects.", inline=False)
    return embed

# ── Embed de config générale ─────────────────────────────────────────
def build_general_embed_page(interaction: discord.Interaction, server_id: int) -> discord.Embed:

    config   = database.get_server_config(server_id) or {}
    channels = database.get_authorized_channels(server_id)

    lang_label = "Français 🇫🇷" if config.get("language", "fr") == "fr" else "English 🇬🇧"
    mode_label = config.get("mode", "défaut").capitalize()
    chan_label  = ", ".join(f"<#{c}>" for c in channels) if channels else "**Aucun salon configuré**"

    embed = _base_embed(interaction, "__Configuration générale__")
    embed.add_field(name=":speech_balloon: • **Description**", value="Panneau de configuration principal du bot. Ici, vous définissez les règles nécessaires à l'activation du bot sur le serveur.", inline=False)
    embed.add_field(name=":speaking_head: • **Langue du serveur**", value=f"> Définie sur: {lang_label}", inline=False)
    embed.add_field(name=":performing_arts: • **Mode conversationnel**", value=f"> Actif: {mode_label}", inline=False)
    embed.add_field(name=":shinto_shrine: • **Salons d'échanges**", value=f"> {chan_label}", inline=False)
    return embed

# ── Embed de config security ─────────────────────────────────────────
def build_security_embed_page(interaction: discord.Interaction, server_id: int) -> discord.Embed:

    config = database.get_server_config(server_id) or {}
    alert_channel = config.get("alertChannel")
    sanction_label = config.get("autoSanction", "Aucune sanction").capitalize()
    notif_label = f"<#{alert_channel}>" if alert_channel else "**Aucun salon défini**"

    embed = _base_embed(interaction, "__Analyse de sécurité__")
    embed.add_field(name=":mag: • **Description**",  value="Il s'agit d'un système anti-scan automatisé. Le bot analysera les liens et images envoyés dans les salons de la configuration générale pour s'assurer qu'ils sont fiables.", inline=False)
    embed.add_field(name=":bookmark: • **Sanction appliquée**", value=f"> **{sanction_label}**", inline=False)
    embed.add_field(name=":envelope_with_arrow: • **Salon de notification**",  value=f"> {notif_label}", inline=False)
    return embed

# ==================================================================================
# ================================ SELECT NAVIGATION ===============================
# ==================================================================================

class PageSelect(discord.ui.Select):

    def __init__(self, interaction: discord.Interaction, server_id: int, current: str):
        self.interaction = interaction
        self.server_id   = server_id

        options = [
            discord.SelectOption(
                label="Page d'accueil",
                value="accueil",
                emoji="🏠",
                default=(current == "accueil")
            ),
            discord.SelectOption(
                label="Configuration générale",
                value="general",
                emoji="⚙️",
                default=(current == "general")
            ),
            discord.SelectOption(
                label="Analyse de sécurité",
                value="security",
                emoji="🛡️",
                default=(current == "security")
            ),
        ]
        super().__init__(
            placeholder="Sélectionnez une section",
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            page = self.values[0]

            if page == "accueil":
                embed = build_accueil_embed_page(interaction)
                view  = AccueilView(interaction, self.server_id)
            elif page == "general":
                embed = build_general_embed_page(interaction, self.server_id)
                view  = GeneralView(interaction, self.server_id)
            elif page == "security":
                embed = build_security_embed_page(interaction, self.server_id)
                view = SecurityView(interaction, self.server_id)
            else:
                return

            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as error:
            logger.error(f"[ERROR CONFIG UI]-> Une erreur s'est produite avec la méthode PageSelect[callback]: {error}", exc_info=True)


# ==================================================================================
# ================================ SELECTS CONFIG GÉNERAL ==========================
# ==================================================================================

class LanguageSelect(discord.ui.Select):
    def __init__(self, server_id: int, current: str):
        self.server_id = server_id
        options = [
            discord.SelectOption(
                label="Français",
                value="fr",
                description="Le prompt système sera rédigé en français",
                emoji="🇫🇷",
                default=(current == "fr")
            ),
            discord.SelectOption(
                label="English",
                value="en",
                description="The system prompt will be written in English",
                emoji="🇬🇧",
                default=(current == "en")
            ),
        ]
        super().__init__(
            placeholder="Choisir une langue...",
            min_values=1,
            max_values=1,
            options=options,
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            database.set_server_config(self.server_id, "language", self.values[0])
            embed = build_general_embed_page(interaction, self.server_id)
            await interaction.response.edit_message(embed=embed)
        except Exception as error:
            logger.error(f"[ERROR CONFIG UI]-> Une erreur s'est produite avec la méthode LanguageSelect[callback]: {error}", exc_info=True)


class ModeSelect(discord.ui.Select):
    def __init__(self, server_id: int, current: str):
        self.server_id = server_id
        is_premium     = database.is_server_premium(server_id)

        options = [
            discord.SelectOption(
                label="Défaut",
                value="défaut",
                description="Comportement standard du bot",
                emoji="🤖",
                default=(current == "défaut")
            ),
        ]

        if is_premium:
            options.append(discord.SelectOption(
                label="Caveman",
                value="caveman",
                description="Style homme des cavernes",
                emoji="⭐",
                default=(current == "caveman")
            )),
            options.append(discord.SelectOption(
                label="Eric Cartman",
                value="cartman",
                description="Personnalité inspirée de Cartman des South Park",
                emoji="⭐",
                default=(current == "cartman")
            )),
            options.append(discord.SelectOption(
                label="Homer Simpson",
                value="homerSimpson",
                description="Personnalité inspirée de Homer simpson des Simpson",
                emoji="⭐",
                default=(current == "homerSimpson")
            )),
            options.append(discord.SelectOption(
                label="Support",
                value="support",
                description="Mode tutoriel. Le bot est strictement lié aux tutoriels du serveur Pc PDL.",
                emoji="🐦‍🔥",
                default=(current == "support")
            ))

        super().__init__(
            placeholder="Choisir un mode...",
            min_values=1,
            max_values=1,
            options=options,
            row=2
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            database.set_server_config(self.server_id, "mode", self.values[0])
            embed = build_general_embed_page(interaction, self.server_id)
            await interaction.response.edit_message(embed=embed)
        except Exception as error:
            logger.error(f"[ERROR CONFIG UI]-> Une erreur s'est produite avec la méthode ModeSelect[callback]: {error}", exc_info=True)


class ChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, server_id: int):
        self.server_id = server_id
        self.limit = 5 if database.is_server_premium(self.server_id) else 2
        super().__init__(
            placeholder="Ajouter / Retirer des salons d'échanges..",
            min_values=1,
            max_values=self.limit,
            channel_types=[discord.ChannelType.text],
            row=3
        )

    async def callback(self, interaction: discord.Interaction):
        try:

            current_channels = database.get_authorized_channels(self.server_id)
            channel_added = 0
            channel_removed = 0

            for channel in self.values:

                if str(channel.id) in current_channels:
                    database.remove_channel(self.server_id, channel.id)
                    current_channels.remove(str(channel.id))
                    channel_removed += 1
                else:
                    if len(current_channels) >= self.limit: continue
                    database.add_channel(self.server_id, channel.id)
                    current_channels.append(str(channel.id))
                    channel_added += 1

            embed = build_general_embed_page(interaction, self.server_id)
            await interaction.response.edit_message(embed=embed)

        except Exception as error:
            logger.error(f"[ERROR CONFIG UI]-> Une erreur s'est produite avec la méthode ChannelSelect[callback]: {error}", exc_info=True)

# ==================================================================================
# ================================ SELECT SECURITY =================================
# ==================================================================================
class AlertChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, server_id: int):
        self.server_id = server_id
        super().__init__(
            placeholder="Sélectionner le salon d'alerte..",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text],
            row=3
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            for channel in self.values:
                database.set_server_config(self.server_id, "alertChannel", channel.id)

            embed = build_security_embed_page(interaction, self.server_id)
            await interaction.response.edit_message(embed=embed)

        except Exception as error:
            logger.error(f"[ERROR CONFIG UI]-> Une erreur s'est produite avec la méthode AlertChannelSelect[callback]: {error}", exc_info=True)

class SanctionSelect(discord.ui.Select):
    def __init__(self, server_id: int, current: str):
        self.server_id = server_id
        is_premium     = database.is_server_premium(server_id)

        options = [
            discord.SelectOption(
                label="Aucune sanction",
                value="Aucune sanction",
                description="Aucune sanction ne sera appliquée.",
                default=(current == "Aucune sanction")
            ),
        ]

        if is_premium:
            options.append(discord.SelectOption(
                label="Avertir",
                value="Avertir",
                description="Avertir l'utilisateur",
                default=(current == "Avertir")
            )),
            options.append(discord.SelectOption(
                label="Rendre muet",
                value="Rendre muet",
                description="Mute l'utilisateur pendant 2 heures",
                default=(current == "Rendre muet")
            )),
            options.append(discord.SelectOption(
                label="Bannir",
                value="Bannir",
                description="Bannir définitivement l'utilisateur",
                default=(current == "Bannir")
            ))

        super().__init__(
            placeholder="Sélectionner la sanction..",
            min_values=1,
            max_values=1,
            options=options,
            row=2
        )
    async def callback(self, interaction: discord.Interaction):
        try:
            database.set_server_config(self.server_id, "autoSanction", self.values[0])
            embed = build_security_embed_page(interaction, self.server_id)
            await interaction.response.edit_message(embed=embed)
        except Exception as error:
            logger.error(f"[ERROR CONFIG UI]-> Une erreur s'est produite avec la méthode SanctionSelect[callback]: {error}", exc_info=True)

# ==================================================================================
# ================================ VIEWS ===========================================
# ==================================================================================


# ── View de la page d'accueil ─────────────────────────────────────────
class AccueilView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, server_id: int):
        super().__init__(timeout=120)
        self.message = None
        self.add_item(PageSelect(interaction, server_id, current="accueil"))

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.Forbidden: pass

# ── View de la page de configuration générale ─────────────────────────────────────────
class GeneralView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, server_id: int):
        super().__init__(timeout=120)
        self.message = None

        config       = database.get_server_config(server_id) or {}
        current_lang = config.get("language", "fr")
        current_mode = config.get("mode", "default")

        self.add_item(PageSelect(interaction, server_id, current="general"))
        self.add_item(LanguageSelect(server_id, current_lang))
        self.add_item(ModeSelect(server_id, current_mode))
        self.add_item(ChannelSelect(server_id))

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.Forbidden: pass

# ── View de la page de configuration générale ─────────────────────────────────────────
class SecurityView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, server_id: int):
        super().__init__(timeout=120)
        self.message = None

        config       = database.get_server_config(server_id) or {}
        current_sanction = config.get("autoSanction", "none")

        self.add_item(PageSelect(interaction, server_id, current="security"))
        self.add_item(SanctionSelect(server_id, current_sanction))
        self.add_item(AlertChannelSelect(server_id))

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.Forbidden: pass