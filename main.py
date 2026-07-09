import os

import colorama
import discord
from discord.ext import commands

from utils import (
    BOT_ROOT_DIR,
    init_clients,
    load_env,
)

colorama.init(autoreset=True)

load_env()
init_clients()
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


if __name__ == "__main__":
    for file in (BOT_ROOT_DIR / "cogs").rglob("*.py"):
        if file.stem == "__init__":
            continue

        bot.load_extension(f"cogs.{file.stem}")

    bot.run(os.environ["discord_bot_token"])
