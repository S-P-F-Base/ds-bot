import asyncio
import contextlib
import os
import sys

import discord
from discord.ext import commands

from .cogs import (
    CommandsCog,
    EventCog,
    ForumControlCog,
    ServerControlCog,
    ValidationCog,
)

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
)

_bot_task: asyncio.Task | None = None
_cogs_loaded = False


async def _run_bot():
    try:
        await bot.start(os.environ["discord_bot"])

    except Exception:
        sys.exit(1)


def _load_cogs():
    global _cogs_loaded

    if _cogs_loaded:
        return

    for cls in [
        CommandsCog,
        EventCog,
        ForumControlCog,
        ServerControlCog,
        ValidationCog,
    ]:
        bot.add_cog(cls(bot))

    _cogs_loaded = True


async def start():
    global _bot_task

    _load_cogs()

    if _bot_task and not _bot_task.done():
        return

    loop = asyncio.get_running_loop()
    _bot_task = loop.create_task(_run_bot())


async def stop():
    global _bot_task

    if bot.is_closed():
        return

    try:
        await bot.close()

        if _bot_task:
            _bot_task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await _bot_task

    except RuntimeError:
        pass
