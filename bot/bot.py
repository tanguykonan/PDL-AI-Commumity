"""Main bot bootstrap: loads command extensions and registers core handlers."""

import asyncio
from bot.client import create_bot
from app.core.main import register_commands

try:
    bot = create_bot()
    if not bot:
        raise Exception("[BOT WARNING] Failed to create bot instance.")

    async def load_cogs():
        """Load all command cogs into the bot instance."""
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
                print(f"[ERROR BOT] Failed to load {cog}: {error}")
                failed_count += 1
        print(f"[INFO BOT] {loaded_count} cog(s) loaded successfully, {failed_count} failed.")

    asyncio.run(load_cogs())
    register_commands(bot)

except Exception as error:
    print(f"[ERROR BOT] Fatal bootstrap error: {error}")
    raise