# ==================================================================================
# ============================ RUNNER DU BOT DISCORD ===============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 30/12/2025
# ==================================================================================
from bot.bot import bot
from colorama import Fore, Style
from settings.config import params

if __name__ == "__main__":
    try:

        if params.DISCORD_TOKEN:
            bot.run(params.DISCORD_TOKEN)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "[WARNING RUN]-> Démarrage arrêté de force." + Style.RESET_ALL)
    except Exception as error:
        print(Fore.RED + f"[ERROR RUN]-> Démarrage échoué: {error}" + Style.RESET_ALL)