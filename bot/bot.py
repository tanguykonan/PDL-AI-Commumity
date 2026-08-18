# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 30/12/2025
# ==================================================================================
import asyncio
# noinspection PyUnresolvedReferences
from bot.client import create_bot
from app.core.main import register_commands

try:
    bot = create_bot()
    if not bot:
        raise Exception("[BOT WARNING]=> Échec de création de l'instance du bot")

    async def load_cogs():
        """Chargement de tous les cogs du bot (Excepter ce de la music)"""
        cogs = [
            "commands.admin.debug",
            "commands.admin.modo",
            "commands.public.help",
            "commands.public.music",
            "commands.public.staff",
            "commands.custom.prefix",
        ]
        
        loaded_count = 0
        failed_count = 0
        
        for cog in cogs:
            try:
                await bot.load_extension(cog)
                loaded_count += 1
            except Exception as error:
                print(f"[ERROR BOT]=> Échec chargement {cog}: {error}")
                failed_count += 1
        print(f"[INFO BOT]-> {loaded_count} cog(s) chargé(s) et  {failed_count} échec(s)")

    asyncio.run(load_cogs())
    register_commands(bot)

except Exception as e:
    print(f"[ERROR BOT]=> Erreur fatale: {e}")
    raise