"""Main entry point for running the PDL-AI Discord bot."""

from bot.bot import bot
from colorama import Fore, Style
from settings.config import params

if __name__ == "__main__":
    try:
        if params.DISCORD_TOKEN:
            bot.run(params.DISCORD_TOKEN)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "[WARNING RUN] Bot execution interrupted by user." + Style.RESET_ALL)
    except Exception as error:
        print(Fore.RED + f"[ERROR RUN] Failed to start bot: {error}" + Style.RESET_ALL)