import json
from typing import Any, cast

from utils import (
    MemoryTools,
    MessageAI,
    ToolManager,
    get_system_prompt,
    logger,
    shared_globals,
)


async def get_ai_response(
    invoke_message: MessageAI,
    context: list[MessageAI],
) -> str:
    logger.debug(f"Запрос от {invoke_message.owner_id}")

    system_prompt = get_system_prompt()

    memory_tools = MemoryTools(
        user_id=invoke_message.owner_id,
        username=invoke_message.owner_name,
    )
    tool_manager = ToolManager(memory_tools)

    messages: list[Any] = [{"role": "system", "content": system_prompt}]

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
        return "Ошибка: клиент ИИ не инициализирован."

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
                    logger.debug(
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

            return content.strip()

    except Exception as e:
        if "insufficient balance" in str(e).lower():
            return "У Каина кончились печеньки в банке. Я не буду отвечать больше"

        logger.exception("Ошибка при обращении к AI")
        return f"Произошла ошибка: {e}"
