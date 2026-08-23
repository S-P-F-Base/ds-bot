import json
import re
from typing import Any, cast

from utils import (
    MemoryTools,
    MessageAI,
    ToolManager,
    get_system_prompt,
    logger,
    shared_globals,
)

MEM_PATTERN = re.compile(r"\[\s*MEM:\s*(.*?)\]", re.IGNORECASE)


async def get_ai_response(
    invoke_message: MessageAI,
    context: list[MessageAI],
) -> str:
    logger.info(f"Запрос от {invoke_message.owner_id}")

    system_prompt = get_system_prompt()

    memory_tools = MemoryTools(
        user_id=invoke_message.owner_id,
        username=invoke_message.owner_name,
    )
    tool_manager = ToolManager(memory_tools)

    messages: list[Any] = [{"role": "system", "content": system_prompt}]
    dynamic_context = await _build_dynamic_context(invoke_message)
    if dynamic_context:
        messages.append({"role": "system", "content": dynamic_context})

    def add_message_to_list(msg: MessageAI):
        role = "assistant" if msg.is_bot else "user"
        content = f"{msg.owner_name}: {msg.message}"
        messages.append({"role": role, "content": content})

    for msg in context:
        add_message_to_list(msg)

    context_keys = {(m.owner_id, m.time, m.message) for m in context}
    for msg in invoke_message.to_list():
        key = (msg.owner_id, msg.time, msg.message)
        if key in context_keys:
            continue

        add_message_to_list(msg)

    client = shared_globals.BOT_AI_CLIENT
    if client is None:
        logger.error("BOT_AI_CLIENT не инициализирован")
        return "Ошибка: ядро ИИ не инициализировано."

    tools_schema = cast(Any, tool_manager.get_tools_schema())

    try:
        while True:
            response = await client.chat.completions.create(
                model="deepseek/deepseek-v4-flash",
                messages=cast(Any, messages),
                tools=tools_schema,
                tool_choice="auto",
            )
            response_message = response.choices[0].message

            if response_message.tool_calls:
                assistant_msg = {
                    "role": "assistant",
                    "content": response_message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": getattr(tool_call, "function").name,
                                "arguments": getattr(tool_call, "function").arguments,
                            },
                        }
                        for tool_call in response_message.tool_calls
                        if hasattr(tool_call, "function")
                    ],
                }
                messages.append(assistant_msg)

                for tool_call in response_message.tool_calls:
                    function = getattr(tool_call, "function", None)
                    if function is None:
                        continue

                    tool_name = function.name
                    arguments = json.loads(function.arguments)
                    logger.info(
                        f"Вызов инструмента: {tool_name} с аргументами {arguments}"
                    )

                    result = await tool_manager.execute(tool_name, arguments)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": str(result),
                        }
                    )

                continue

            content = response_message.content
            if content is None:
                return "Пустой ответ от модели."

            content = _extract_and_save_mem(content)
            content = _sanitize_text(content)
            return content.lstrip("Анна:").strip()  # noqa: B005

    except Exception as e:
        if "insufficient balance" in str(e).lower():
            return "У Каина кончились печеньки в банке. Я не буду отвечать больше"

        logger.exception("Ошибка при обращении к AI")
        return f"Произошла ошибка: {e}"


def _extract_and_save_mem(text: str) -> str:
    matches = list(MEM_PATTERN.finditer(text))
    if not matches:
        return text

    for match in matches:
        memory_text = match.group(1).strip()
        if memory_text:
            shared_globals.BOT_MEMORY_DB.add_global_memory(memory_text)
            logger.info(f"Автосохранение из ответа Анны: {memory_text}")

    return MEM_PATTERN.sub("", text).strip()


async def _build_dynamic_context(invoke_message: MessageAI) -> str:
    db = shared_globals.BOT_MEMORY_DB
    user_id = invoke_message.owner_id
    username = invoke_message.owner_name

    parts = []

    user = db.get_user(user_id)
    if user is None:
        db.upsert_user(user_id, username)
        user = db.get_user(user_id)

    score = 0
    if user:
        score = int(user.get("relationship_score") or 0)

    if score >= 50:
        desc = "очень близкий человек"
    elif score >= 20:
        desc = "симпатичен, нравится общаться"
    elif score >= -10:
        desc = "нейтрально, просто знакомый"
    elif score >= -50:
        desc = "раздражает, но терпимо"
    else:
        desc = "вызывает сильную неприязнь"

    parts.append(f"Твоё текущее отношение к {username}: {desc} (score={score}).")

    notes = db.get_user_notes(user_id, limit=3)
    if notes:
        parts.append(
            "Твои заметки об этом пользователе:\n" + "\n".join(f"- {n}" for n in notes)
        )

    memories = db.get_all_global_memories(limit=5)
    if memories:
        parts.append(
            "Твои последние глобальные воспоминания:\n"
            + "\n".join(f"- {m}" for m in memories)
        )

    return "\n\n".join(parts)


def _sanitize_text(text: str) -> str:
    replacements = {
        "«": '"',
        "»": '"',
        "„": '"',
        "“": '"',
        "—": "-",
        "–": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    return text
