from utils import MessageAI, logger


async def get_ai_response(
    user_message: MessageAI,
) -> str:
    logger.debug(f"Запрос от {user_message.owner_id}")

    return f"<:oh_no:1518918162912116868>\n```\n{user_message!r}\n```"
