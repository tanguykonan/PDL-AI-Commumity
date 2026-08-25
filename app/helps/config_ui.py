"""Interactive Discord UI components and Embed builders for server configuration."""

import datetime
import discord
from app.helps.utils import logger
from plugins.integrating.storing.database import database


def _base_embed(interaction: discord.Interaction, title: str) -> discord.Embed:
    """Build a standard base embed with server author and timestamp."""
    embed = discord.Embed(title=title, color=discord.Color.red())

    if interaction.guild and interaction.guild.icon:
        embed.set_author(name="Server Configuration", icon_url=interaction.guild.icon.url)
        embed.set_thumbnail(url=interaction.guild.icon.url)

    embed.set_footer(
        text=f"Requested by @{interaction.user.name}",
        icon_url=interaction.user.display_avatar.url,
    )
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    return embed


def build_accueil_embed_page(interaction: discord.Interaction) -> discord.Embed:
    """Build the configuration home page embed."""
    embed = _base_embed(interaction, "__Home Page__")
    embed.add_field(
        name=":gear: • **General Configuration**",
        value="Global interaction settings: language, AI persona mode, discussion channels.",
        inline=False,
    )
    embed.add_field(
        name=":shield: • **Security Analysis**",
        value="Automated link and media scanning: detect harmful or suspicious content.",
        inline=False,
    )
    return embed


def build_general_embed_page(interaction: discord.Interaction, server_id: int) -> discord.Embed:
    """Build the general settings page embed."""
    config = database.get_server_config(server_id) or {}
    channels = database.get_authorized_channels(server_id)

    lang_label = "Français 🇫🇷" if config.get("language", "fr") == "fr" else "English 🇬🇧"
    mode_label = config.get("mode", "défaut").capitalize()
    chan_label = ", ".join(f"<#{c}>" for c in channels) if channels else "**No channels configured**"

    embed = _base_embed(interaction, "__General Configuration__")
    embed.add_field(
        name=":speech_balloon: • **Description**",
        value="Main bot configuration panel. Define the rules required for the bot to interact on your server.",
        inline=False,
    )
    embed.add_field(name=":speaking_head: • **Server Language**", value=f"> Set to: {lang_label}", inline=False)
    embed.add_field(name=":performing_arts: • **Conversational Mode**", value=f"> Active: {mode_label}", inline=False)
    embed.add_field(name=":shinto_shrine: • **Active Channels**", value=f"> {chan_label}", inline=False)
    return embed


def build_security_embed_page(interaction: discord.Interaction, server_id: int) -> discord.Embed:
    """Build the security settings page embed."""
    config = database.get_server_config(server_id) or {}
    alert_channel = config.get("alertChannel")
    sanction_label = config.get("autoSanction", "No sanction").capitalize()
    notif_label = f"<#{alert_channel}>" if alert_channel else "**No channel defined**"

    embed = _base_embed(interaction, "__Security Analysis__")
    embed.add_field(
        name=":mag: • **Description**",
        value="Automated security scanner. Analyzes links and images in authorized channels to ensure safety.",
        inline=False,
    )
    embed.add_field(name=":bookmark: • **Applied Sanction**", value=f"> **{sanction_label}**", inline=False)
    embed.add_field(name=":envelope_with_arrow: • **Alert Channel**", value=f"> {notif_label}", inline=False)
    return embed


class PageSelect(discord.ui.Select):
    """Navigation select menu across configuration pages."""

    def __init__(self, interaction: discord.Interaction, server_id: int, current: str):
        self.interaction = interaction
        self.server_id = server_id

        options = [
            discord.SelectOption(
                label="Home Page",
                value="accueil",
                emoji="🏠",
                default=(current == "accueil"),
            ),
            discord.SelectOption(
                label="General Configuration",
                value="general",
                emoji="⚙️",
                default=(current == "general"),
            ),
            discord.SelectOption(
                label="Security Analysis",
                value="security",
                emoji="🛡️",
                default=(current == "security"),
            ),
        ]
        super().__init__(
            placeholder="Select a section...",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            page = self.values[0]

            if page == "accueil":
                embed = build_accueil_embed_page(interaction)
                view = AccueilView(interaction, self.server_id)
            elif page == "general":
                embed = build_general_embed_page(interaction, self.server_id)
                view = GeneralView(interaction, self.server_id)
            elif page == "security":
                embed = build_security_embed_page(interaction, self.server_id)
                view = SecurityView(interaction, self.server_id)
            else:
                return

            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as error:
            logger.error(f"[ERROR CONFIG UI] Error in PageSelect callback: {error}", exc_info=True)


class LanguageSelect(discord.ui.Select):
    """Language selection component."""

    def __init__(self, server_id: int, current: str):
        self.server_id = server_id
        options = [
            discord.SelectOption(
                label="Français",
                value="fr",
                description="Le prompt système sera rédigé en français",
                emoji="🇫🇷",
                default=(current == "fr"),
            ),
            discord.SelectOption(
                label="English",
                value="en",
                description="The system prompt will be written in English",
                emoji="🇬🇧",
                default=(current == "en"),
            ),
        ]
        super().__init__(
            placeholder="Choose language...",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            database.set_server_config(self.server_id, "language", self.values[0])
            embed = build_general_embed_page(interaction, self.server_id)
            await interaction.response.edit_message(embed=embed)
        except Exception as error:
            logger.error(f"[ERROR CONFIG UI] Error in LanguageSelect callback: {error}", exc_info=True)


class ModeSelect(discord.ui.Select):
    """Persona mode selection component."""

    def __init__(self, server_id: int, current: str):
        self.server_id = server_id
        is_premium = database.is_server_premium(server_id)

        options = [
            discord.SelectOption(
                label="Défaut",
                value="défaut",
                description="Comportement standard du bot",
                emoji="🤖",
                default=(current == "défaut"),
            ),
        ]

        if is_premium:
            options.append(
                discord.SelectOption(
                    label="Caveman",
                    value="caveman",
                    description="Primitive caveman style",
                    emoji="⭐",
                    default=(current == "caveman"),
                )
            )
            options.append(
                discord.SelectOption(
                    label="Eric Cartman",
                    value="cartman",
                    description="Sarcastic persona inspired by South Park",
                    emoji="⭐",
                    default=(current == "cartman"),
                )
            )
            options.append(
                discord.SelectOption(
                    label="Homer Simpson",
                    value="homerSimpson",
                    description="Casual persona inspired by The Simpsons",
                    emoji="⭐",
                    default=(current == "homerSimpson"),
                )
            )
            options.append(
                discord.SelectOption(
                    label="Support",
                    value="support",
                    description="Strict technical tutorial assistant",
                    emoji="🔥",
                    default=(current == "support"),
                )
            )

        super().__init__(
            placeholder="Choose a mode...",
            min_values=1,
            max_values=1,
            options=options,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            database.set_server_config(self.server_id, "mode", self.values[0])
            embed = build_general_embed_page(interaction, self.server_id)
            await interaction.response.edit_message(embed=embed)
        except Exception as error:
            logger.error(f"[ERROR CONFIG UI] Error in ModeSelect callback: {error}", exc_info=True)


class ChannelSelect(discord.ui.ChannelSelect):
    """Active channels multi-select component."""

    def __init__(self, server_id: int):
        self.server_id = server_id
        self.limit = 5 if database.is_server_premium(self.server_id) else 2
        super().__init__(
            placeholder="Add or remove discussion channels...",
            min_values=1,
            max_values=self.limit,
            channel_types=[discord.ChannelType.text],
            row=3,
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
                    if len(current_channels) >= self.limit:
                        continue
                    database.add_channel(self.server_id, channel.id)
                    current_channels.append(str(channel.id))
                    channel_added += 1

            embed = build_general_embed_page(interaction, self.server_id)
            await interaction.response.edit_message(embed=embed)
        except Exception as error:
            logger.error(f"[ERROR CONFIG UI] Error in ChannelSelect callback: {error}", exc_info=True)


class AlertChannelSelect(discord.ui.ChannelSelect):
    """Security alert channel select component."""

    def __init__(self, server_id: int):
        self.server_id = server_id
        super().__init__(
            placeholder="Select alert channel...",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text],
            row=3,
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            for channel in self.values:
                database.set_server_config(self.server_id, "alertChannel", channel.id)

            embed = build_security_embed_page(interaction, self.server_id)
            await interaction.response.edit_message(embed=embed)
        except Exception as error:
            logger.error(f"[ERROR CONFIG UI] Error in AlertChannelSelect callback: {error}", exc_info=True)


class SanctionSelect(discord.ui.Select):
    """Security auto-sanction select component."""

    def __init__(self, server_id: int, current: str):
        self.server_id = server_id
        is_premium = database.is_server_premium(server_id)

        options = [
            discord.SelectOption(
                label="Aucune sanction",
                value="Aucune sanction",
                description="No sanction will be applied.",
                default=(current == "Aucune sanction"),
            ),
        ]

        if is_premium:
            options.append(
                discord.SelectOption(
                    label="Avertir",
                    value="Avertir",
                    description="Warn the user",
                    default=(current == "Avertir"),
                )
            )
            options.append(
                discord.SelectOption(
                    label="Rendre muet",
                    value="Rendre muet",
                    description="Mute user for 2 hours",
                    default=(current == "Rendre muet"),
                )
            )
            options.append(
                discord.SelectOption(
                    label="Bannir",
                    value="Bannir",
                    description="Permanently ban the user",
                    default=(current == "Bannir"),
                )
            )

        super().__init__(
            placeholder="Select sanction...",
            min_values=1,
            max_values=1,
            options=options,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            database.set_server_config(self.server_id, "autoSanction", self.values[0])
            embed = build_security_embed_page(interaction, self.server_id)
            await interaction.response.edit_message(embed=embed)
        except Exception as error:
            logger.error(f"[ERROR CONFIG UI] Error in SanctionSelect callback: {error}", exc_info=True)


class AccueilView(discord.ui.View):
    """Home view for configuration panel."""

    def __init__(self, interaction: discord.Interaction, server_id: int):
        super().__init__(timeout=120)
        self.message = None
        self.add_item(PageSelect(interaction, server_id, current="accueil"))

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.Forbidden:
                pass


class GeneralView(discord.ui.View):
    """General configuration view."""

    def __init__(self, interaction: discord.Interaction, server_id: int):
        super().__init__(timeout=120)
        self.message = None

        config = database.get_server_config(server_id) or {}
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
            except discord.Forbidden:
                pass


class SecurityView(discord.ui.View):
    """Security configuration view."""

    def __init__(self, interaction: discord.Interaction, server_id: int):
        super().__init__(timeout=120)
        self.message = None

        config = database.get_server_config(server_id) or {}
        current_sanction = config.get("autoSanction", "none")

        self.add_item(PageSelect(interaction, server_id, current="security"))
        self.add_item(SanctionSelect(server_id, current_sanction))
        self.add_item(AlertChannelSelect(server_id))

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.Forbidden:
                pass