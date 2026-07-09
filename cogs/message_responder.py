import discord
from discord.ext import commands

from handlers import get_ai_response
from utils import MessageAI, logger


class MessageResponder(commands.Cog):
    BOT_NAMES = frozenset({"анна", "аня", "анечка", "аннушка", "анютка", "скайнет"})
    MAX_REFERENCE_DEPTH = 4
    CONTEXT_LIMIT = 10

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not self._is_addressed_to_bot(message):
            return

        if not isinstance(message.channel, discord.TextChannel):
            return

        user_msg = await self._build_message_ai(message, depth=0)

        context = await self._get_channel_context(
            channel=message.channel,
            exclude_message_id=message.id,
            limit=self.CONTEXT_LIMIT,
        )

        async with message.channel.typing():
            response = await get_ai_response(user_msg, context)

        await self._reply_with_split(message, response, mention_author=True)

    async def _get_channel_context(
        self,
        channel: discord.TextChannel,
        exclude_message_id: int,
        limit: int = 10,
    ) -> list[MessageAI]:
        messages = []
        async for msg in channel.history(limit=limit * 2):
            if msg.id == exclude_message_id:
                continue

            if len(msg.content.strip()) < 3:
                continue

            ai_msg = MessageAI(
                owner_id=msg.author.id,
                owner_name=msg.author.display_name,
                message=msg.content,
                time=msg.created_at.strftime("%d.%m %H:%M"),
                reference=None,
            )
            messages.append(ai_msg)
            if len(messages) >= limit:
                break

        messages.reverse()
        return messages

    async def _build_message_ai(self, msg: discord.Message, depth: int) -> MessageAI:
        if depth >= self.MAX_REFERENCE_DEPTH:
            return MessageAI(
                owner_id=0,
                owner_name="система",
                message="[скрыто: слишком глубокий контекст]",
                time=msg.created_at.strftime("%d.%m %H:%M"),
                reference=None,
            )

        reference_msg = None
        if msg.reference:
            if msg.reference.resolved and isinstance(
                msg.reference.resolved, discord.Message
            ):
                reference_msg = msg.reference.resolved

            elif msg.reference.message_id:
                try:
                    reference_msg = await msg.channel.fetch_message(
                        msg.reference.message_id
                    )

                except discord.NotFound:
                    logger.debug(f"Сообщение {msg.reference.message_id} не найдено")

                except Exception as e:
                    logger.debug(f"Ошибка fetch: {e}")

        ref_ai = None
        if reference_msg:
            ref_ai = await self._build_message_ai(reference_msg, depth + 1)

        return MessageAI(
            owner_id=msg.author.id,
            owner_name=msg.author.display_name,
            message=msg.content,
            time=msg.created_at.strftime("%d.%m %H:%M"),
            reference=ref_ai,
        )

    def _is_addressed_to_bot(self, message: discord.Message) -> bool:
        if self.bot.user.mentioned_in(message):
            return True

        if message.reference and message.reference.resolved:
            if isinstance(message.reference.resolved, discord.Message):
                if message.reference.resolved.author == self.bot.user:
                    return True

        content_lower = message.content.lower().strip()
        for name in self.BOT_NAMES:
            if content_lower.startswith(name):
                return True

        return False

    async def _reply_with_split(
        self,
        message: discord.Message,
        text: str,
        mention_author: bool = True,
    ):
        if len(text) <= 1900:
            await message.reply(text, mention_author=mention_author)
            return

        parts = self._split_text(text, max_length=1900)
        for i, part in enumerate(parts):
            if i == 0:
                await message.reply(part, mention_author=mention_author)

            else:
                await message.channel.send(part)

    def _split_text(self, text: str, max_length: int = 1900) -> list:
        parts = []
        while len(text) > max_length:
            split_pos = -1
            pos = text.rfind("\n\n", 0, max_length)
            if pos != -1:
                split_pos = pos + 2

            else:
                pos = text.rfind("\n", 0, max_length)
                if pos != -1:
                    split_pos = pos + 1

                else:
                    pos = text.rfind(" ", 0, max_length)
                    if pos != -1:
                        split_pos = pos + 1

                    else:
                        split_pos = max_length

            parts.append(text[:split_pos].strip())
            text = text[split_pos:].lstrip()

        if text:
            parts.append(text.strip())

        return parts


def setup(bot):
    bot.add_cog(MessageResponder(bot))
