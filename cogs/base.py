import discord
from discord.ext import commands

from utils import logger


class BaseCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"{self.bot.user.name} готова!")  # type: ignore

    @commands.command("ping")
    async def ping(self, ctx):
        await ctx.send("Pong!")


def setup(bot: discord.Bot):
    bot.add_cog(BaseCog(bot))
