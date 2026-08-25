"""Discord client initialization and intents configuration."""

import discord
from discord.ext import commands
from settings.config import params


def create_bot() -> commands.Bot:
    """Create and configure the Discord bot instance with required intents."""
    try:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.voice_states = True

        bot = commands.Bot(command_prefix=params.PREFIX, help_command=None, intents=intents)
        if not bot:
            print("[WARNING CLIENT] Bot instance could not be created.")
        return bot

    except Exception as error:
        print(f"[ERROR CLIENT] Failed to initialize bot instance: {error}")
        return None