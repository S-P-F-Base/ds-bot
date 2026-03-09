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

        if (
            "Одобрено" in embed.fields[index].value
            or "Отклонено" in embed.fields[index].value
        ):
            await interaction.response.send_message("Уже проверено.", ephemeral=True)
            return

        ts = int(time.time())

        if approved:
            value = f"Одобрено: {interaction.user.mention}\n<t:{ts}:f> (<t:{ts}:R>)"  # type: ignore
        else:
            value = f"Отклонено: {interaction.user.mention}\n<t:{ts}:f> (<t:{ts}:R>)"  # type: ignore

        embed.set_field_at(
            index,
            name=stage_name,
            value=value,
            inline=False,
        )

        if not approved:
            embed.colour = Colour.red()

        all_done = all(
            ("Ожидает проверки" not in f.value and "Отклонено" not in f.value)
            for f in embed.fields
        )

        if all_done:
            embed.colour = Colour.green()

        await interaction.response.edit_message(embed=embed, view=self)

        if all_done:
            await interaction.channel.send("Проверка анкеты завершена.")  # type: ignore

    @discord.ui.button(label="TEX ✓", style=discord.ButtonStyle.blurple)
    async def tex_ok(self, button, interaction):
        await self._apply(interaction, "tex", True)

    @discord.ui.button(label="TEX ✗", style=discord.ButtonStyle.red)
    async def tex_no(self, button, interaction):
        await self._apply(interaction, "tex", False)

    @discord.ui.button(label="LOR ✓", style=discord.ButtonStyle.blurple)
    async def lor_ok(self, button, interaction):
        await self._apply(interaction, "lor", True)

    @discord.ui.button(label="LOR ✗", style=discord.ButtonStyle.red)
    async def lor_no(self, button, interaction):
        await self._apply(interaction, "lor", False)

    @discord.ui.button(label="FIN ✓", style=discord.ButtonStyle.green)
    async def fin_ok(self, button, interaction):
        await self._apply(interaction, "fin", True)

    @discord.ui.button(label="FIN ✗", style=discord.ButtonStyle.red)
    async def fin_no(self, button, interaction):
        await self._apply(interaction, "fin", False)


class ValidationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def build_embed(self) -> Embed:
        embed = Embed(
            title="Проверка анкеты",
            colour=Colour.red(),
            timestamp=discord.utils.utcnow(),
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

        embed.set_footer(text="Система проверки анкеты")

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
