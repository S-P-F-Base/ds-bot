import time

import discord
from discord import Colour, Embed
from discord.ext import commands

from .etc import ALLOWED_ROLES

STAGES = {
    "tex": (0, "Техническая часть"),
    "lor": (1, "Лорная часть"),
    "fin": (2, "Финальная часть"),
}


PENDING = "Ожидает проверки"
APPROVED = "Одобрено"
REJECTED = "Отклонено"


class ValidationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _apply(
        self,
        interaction: discord.Interaction,
        stage: str,
        approved: bool,
    ):
        if not any(r.id in ALLOWED_ROLES for r in interaction.user.roles):  # type: ignore
            await interaction.response.send_message("Нет прав.", ephemeral=True)
            return

        msg = interaction.message
        if msg is None or not msg.embeds:
            return

        embed = msg.embeds[0]

        index, stage_name = STAGES[stage]
        field = embed.fields[index]

        if APPROVED in field.value or REJECTED in field.value:
            await interaction.response.send_message(
                "Этот этап уже проверен.",
                ephemeral=True,
            )
            return

        ts = int(time.time())

        if approved:
            value = f"{APPROVED}: {interaction.user.mention}\n<t:{ts}:f> (<t:{ts}:R>)"  # type: ignore
        else:
            value = f"{REJECTED}: {interaction.user.mention}\n<t:{ts}:f> (<t:{ts}:R>)"  # type: ignore

        embed.set_field_at(
            index,
            name=stage_name,
            value=value,
            inline=False,
        )

        rejected = any(REJECTED in f.value for f in embed.fields)
        approved_all = all(APPROVED in f.value for f in embed.fields)

        if rejected:
            embed.colour = Colour.red()
            self.clear_items()

        elif approved_all:
            embed.colour = Colour.green()
            self.clear_items()

        else:
            embed.colour = Colour.yellow()

        await interaction.response.edit_message(embed=embed, view=self)

        if approved_all:
            await interaction.channel.send("Проверка анкеты завершена")  # type: ignore

    # TEX
    @discord.ui.button(label="TEX ✓ ", style=discord.ButtonStyle.blurple, row=0)
    async def tex_ok(self, button, interaction):
        await self._apply(interaction, "tex", True)

    @discord.ui.button(label="TEX ✗ ", style=discord.ButtonStyle.red, row=0)
    async def tex_no(self, button, interaction):
        await self._apply(interaction, "tex", False)

    # LOR
    @discord.ui.button(label="LOR ✓ ", style=discord.ButtonStyle.blurple, row=1)
    async def lor_ok(self, button, interaction):
        await self._apply(interaction, "lor", True)

    @discord.ui.button(label="LOR ✗ ", style=discord.ButtonStyle.red, row=1)
    async def lor_no(self, button, interaction):
        await self._apply(interaction, "lor", False)

    # FIN
    @discord.ui.button(label="FIN ✓ ", style=discord.ButtonStyle.green, row=2)
    async def fin_ok(self, button, interaction):
        await self._apply(interaction, "fin", True)

    @discord.ui.button(label="FIN ✗ ", style=discord.ButtonStyle.red, row=2)
    async def fin_no(self, button, interaction):
        await self._apply(interaction, "fin", False)


class ValidationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def build_embed(self) -> Embed:
        embed = Embed(
            title="Проверка анкеты",
            colour=Colour.yellow(),
            timestamp=discord.utils.utcnow(),
        )

        embed.add_field(
            name="Техническая часть",
            value=PENDING,
            inline=False,
        )

        embed.add_field(
            name="Лорная часть",
            value=PENDING,
            inline=False,
        )

        embed.add_field(
            name="Финальная часть",
            value=PENDING,
            inline=False,
        )

        embed.set_footer(text="Время создания проверки")

        return embed

    @commands.command(name="validation")
    async def create_validation(self, ctx: commands.Context):
        if not any(r.id in ALLOWED_ROLES for r in ctx.author.roles):  # type: ignore
            return

        embed = self.build_embed()

        await ctx.send(
            embed=embed,
            view=ValidationView(),
        )
