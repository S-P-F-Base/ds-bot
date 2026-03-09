from discord import Colour, Embed
from discord.ext import commands

from .etc import ALLOWED_ROLES

STAGES = {
    "tex": (0, "Техническая часть"),
    "lor": (1, "Лорная часть"),
    "fin": (2, "Финальная часть"),
}


class ValidationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def build_embed(self) -> Embed:
        embed = Embed(
            title="Проверка анкеты",
            colour=Colour.orange(),
        )

        embed.add_field(
            name="Техническая часть",
            value="Ожидает проверки",
            inline=False,
        )

        embed.add_field(
            name="Лорная часть",
            value="Ожидает проверки",
            inline=False,
        )

        embed.add_field(
            name="Финальная часть",
            value="Ожидает проверки",
            inline=False,
        )

        return embed

    @commands.command(name="validation")
    async def create_validation(self, ctx: commands.Context):
        """Создать карточку проверки"""

        if not any(r.id in ALLOWED_ROLES for r in ctx.author.roles):  # type: ignore
            return

        embed = self.build_embed()
        await ctx.send(embed=embed)

    @commands.command(name="validate")
    async def validate(self, ctx: commands.Context, stage: str):
        """!validate tex|lor|fin"""

        if ctx.guild is None:
            return

        if not any(r.id in ALLOWED_ROLES for r in ctx.author.roles):  # type: ignore
            await ctx.message.delete()
            return

        if not ctx.message.reference:
            await ctx.message.delete()
            return

        stage = stage.lower().strip()

        if stage not in STAGES:
            await ctx.message.delete()
            return

        index, stage_name = STAGES[stage]

        ref = ctx.message.reference
        msg = await ctx.channel.fetch_message(ref.message_id)  # type: ignore

        if not msg.embeds:
            await ctx.message.delete()
            return

        embed = msg.embeds[0]

        embed.set_field_at(
            index,
            name=f"{stage_name} ({stage.upper()})",
            value=f"Проверено: {ctx.author.mention}",
            inline=False,
        )

        await msg.edit(embed=embed)

        await ctx.message.delete()
