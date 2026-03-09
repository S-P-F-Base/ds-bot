import os

import discord
from discord.ext import commands

from .cogs import (
    CommandsCog,
    EventCog,
    ForumControlCog,
    ServerControlCog,
)

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


async def start():
    for cls in [
        CommandsCog,
        EventCog,
        ForumControlCog,
        ServerControlCog,
    ]:
        bot.add_cog(cls(bot))

    await bot.start(os.environ["discord_bot"])


async def stop():
    await bot.close()
