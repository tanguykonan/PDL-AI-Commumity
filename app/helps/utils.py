# ==================================================================================
# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 30/12/2025
# ==================================================================================
import logging
import discord
from colorama import Fore, Style
from settings.config import params


class MyDecorators:
    def __init__(self):
        pass

mydecorators = MyDecorators()

class UsefulMethods:
    @staticmethod
    def debug():
        loggers = logging.getLogger('cartman')
        loggers.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        try:
            err_handler = logging.FileHandler(params.ERROR_PATH)
            err_handler.setLevel(logging.ERROR)
            err_handler.setFormatter(formatter)
            err_handler.addFilter(lambda record: record.levelno == logging.ERROR)
            loggers.addHandler(err_handler)

            warn_handler = logging.FileHandler(params.WARNING_PATH)
            warn_handler.setLevel(logging.WARNING)
            warn_handler.setFormatter(formatter)
            warn_handler.addFilter(lambda record: record.levelno == logging.WARNING)
            loggers.addHandler(warn_handler)
        except Exception as error:
            print(f"[ERROR UTILS]-> Une erreur est survenue au niveau du système de logging: {error}")
        return loggers

    @staticmethod
    async def check_is_guild(interaction: discord.Interaction) -> bool:
        """Vérifier que la commande est executée dans un serveur"""
        if interaction.guild is None:
            return False
        return True

    @staticmethod
    def check_is_support_member(user_id: int) -> bool:
        """Vérifier que l'utilisateur est membre du support"""
        support_member = [int(x.strip()) for x in params.SUPPORT_MEMBERS.strip("()").split(",")]
        return user_id in support_member

logger = UsefulMethods().debug()