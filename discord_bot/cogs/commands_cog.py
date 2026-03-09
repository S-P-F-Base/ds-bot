import discord
from discord import Colour, Embed
from discord.ext import commands

from .etc import CAIN_ID, REACTION_NO, REACTION_YES

ALLOWED_ROLES = {
    1361481568404766780,  # Сержант
    1450999978419027989,  # Лейтинант
    1322091700813955084,  # Ст. админ
    1414370801318105188,  # Ст. модер
    1321537454645448716,  # Гл. спф
    1353426520915579060,  # Расист
    1402602828387844177,  # Тех админ
    1355456288716488854,  # Бот
}

TEAM_ROLES = {
    "0": 1430944877721423916,
    "1": 1430944267492393123,
    "2": 1430944532475805746,
    "3": 1430944606324916334,
    "4": 1430944655561723944,
    "5": 1430944692018610207,
}


class CommandsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="limits")
    async def limits_cmd(self, ctx: commands.Context):
        author_id = ctx.author.id
        if not author_id:
            return

        await ctx.send(
            "Кайн отобрал у меня доступ к базе данных...\nЯ не могу сейчас что либо сказать.",
            file=discord.File("images/ashley/worry.png"),
        )

    @commands.command(name="help")
    async def help_cmd(self, ctx: commands.Context):
        user_embed = Embed(title="Команды для игроков", colour=Colour.orange())
        user_embed.add_field(
            name="",
            value="\n".join(
                [
                    "`!help` - Показать справку по командам",
                ]
            ),
            inline=False,
        )

        team_embed = Embed(title="Команды для сержантов", colour=Colour.yellow())
        team_embed.add_field(
            name="",
            value="\n".join(
                [
                    "`!team <user> <0|1|2|3|4|5> [add|remove]`",
                    "Добавить или убрать пользователя из отряда.",
                    "",
                    "**Примеры:**",
                    "`!team @User 3` — добавить в отряд 3",
                    "`!team @User 3 remove` — убрать из отряда 3",
                ]
            ),
            inline=False,
        )

        admin_embed = Embed(title="Команды для администрации", colour=Colour.red())
        admin_embed.add_field(
            name="",
            value="\n".join(
                [
                    "`!server <start|stop|restart|status>` - Управление сервером",
                    "`!cleanup` - Чистка мусора с анкет",
                ]
            ),
            inline=False,
        )

        await ctx.send(embeds=[user_embed, team_embed, admin_embed])

    @commands.command(name="team")
    async def team_cmd(
        self,
        ctx: commands.Context,
        member: discord.Member,
        team: str,
        action: str = "add",
    ):
        guild = ctx.guild
        if guild is None:
            await ctx.send("Эта команда доступна только на сервере.")
            return

        author: discord.Member = ctx.author  # type: ignore[assignment]

        author_roles = {r.id for r in author.roles}
        if not (author_roles & ALLOWED_ROLES):
            await ctx.message.add_reaction(REACTION_NO)
            return

        team = team.lower().strip()
        action = action.lower().strip()

        if team not in TEAM_ROLES:
            await ctx.message.add_reaction(REACTION_NO)
            await ctx.send("Неверный номер отряда. Используйте 0–5.")
            return

        if action not in ("add", "remove"):
            await ctx.message.add_reaction(REACTION_NO)
            await ctx.send("Неверное действие. Используйте add или remove.")
            return

        target_role = guild.get_role(TEAM_ROLES[team])
        if target_role is None:
            await ctx.message.add_reaction(REACTION_NO)
            await ctx.send("Роль отряда не найдена на сервере.")
            return

        if action == "remove":
            if target_role not in member.roles:
                await ctx.message.add_reaction(REACTION_NO)
                return

            await member.remove_roles(
                target_role,
                reason=f"team remove {team} by {author}",
            )
            await ctx.message.add_reaction(REACTION_YES)
            return

        # add
        if target_role in member.roles:
            await ctx.message.add_reaction(REACTION_NO)
            return

        await member.add_roles(
            target_role,
            reason=f"team add {team} by {author}",
        )
        await ctx.message.add_reaction(REACTION_YES)

    @commands.command(name="wtf")
    async def wtf(self, ctx: commands.Context, member: discord.Member):
        author_id = ctx.author.id
        if author_id != CAIN_ID:
            await ctx.message.add_reaction(REACTION_NO)
            return

        created_ts = int(member.created_at.timestamp())
        joined_ts = int(member.joined_at.timestamp()) if member.joined_at else None

        embed = Embed(
            title="Информация о пользователе",
            colour=Colour.orange(),
        )

        embed.add_field(
            name="Аккаунт создан",
            value=f"<t:{created_ts}:f>\n(<t:{created_ts}:R>)",
            inline=False,
        )

        if joined_ts:
            embed.add_field(
                name="Присоединился к серверу",
                value=f"<t:{joined_ts}:f>\n(<t:{joined_ts}:R>)",
                inline=False,
            )

            delta = member.joined_at - member.created_at  # type: ignore
            total_seconds = int(delta.total_seconds())

            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            parts = []
            if days:
                parts.append(f"{days}д")

            if hours:
                parts.append(f"{hours}ч")

            if minutes:
                parts.append(f"{minutes}м")

            if seconds:
                parts.append(f"{seconds}с")

            pretty_delta = " ".join(parts) if parts else "< 1с"

            embed.add_field(
                name="Время между созданием и входом",
                value=pretty_delta,
                inline=False,
            )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")

        await ctx.send(embed=embed)
