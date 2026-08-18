# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 02/01/2026
# ==================================================================================
import discord
from discord.ext import commands
from settings.config import params

def create_bot():
    try:
        intents: discord.Intents = discord.Intents.default()
        intents.message_content = True # noqa
        intents.members = True # noqa
        intents.guilds = True # noqa
        intents.voice_states = True # noqa
        bot = commands.Bot(command_prefix=params.PREFIX, help_command=None, intents=intents)
        if not bot:
            print(f"[WARNING CLIENT]-> L'instance du bot n'a pas été crée")
        return bot

    except Exception as error:
        print(f"[ERROR CLIENT]-> Une erreur s'est produite à la création du bot: {error}")
        return None