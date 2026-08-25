"""Logging setup and utility helper methods."""
import os
import logging
import discord
from colorama import Fore, Style
from settings.config import params


class MyDecorators:
    def __init__(self):
        pass


mydecorators = MyDecorators()


class UsefulMethods:

    def _verify_path(self, path):
        """Vérifie et crée le dossier parent si nécessaire."""
        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

    def debug(self) -> logging.Logger:
        """Configure and return the file logging handler."""
        self._verify_path(params.ERROR_PATH)
        self._verify_path(params.WARNING_PATH)

        loggers = logging.getLogger("pdl-ai")
        loggers.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

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
            print(f"[ERROR UTILS] Failed to configure logging handlers: {error}")
        return loggers

    @staticmethod
    async def check_is_guild(interaction: discord.Interaction) -> bool:
        """Check if the interaction was executed within a Discord guild."""
        if interaction.guild is None:
            return False
        return True

    @staticmethod
    def check_is_support_member(user_id: int) -> bool:
        """Check if the specified user ID belongs to the support team."""
        if not params.SUPPORT_MEMBERS:
            return False
        support_members = [int(x.strip()) for x in params.SUPPORT_MEMBERS.strip("()").split(",") if x.strip()]
        return user_id in support_members


logger = UsefulMethods().debug()