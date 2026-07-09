from utils import MessageAI, logger


async def get_ai_response(
    invoke_message: MessageAI,
    context: list[MessageAI],
) -> str:
    logger.debug(f"Запрос от {invoke_message.owner_id}")

    context_msg = ""
    for msg in context:
        context_msg += repr(msg) + "\n"

    return (
        f"<:oh_no:1518918162912116868>\n\n"
        f"Invoke message:\n```\n{invoke_message!r}\n```\n\n"
        f"Context:\n```\n{context_msg}\n```"
    )
