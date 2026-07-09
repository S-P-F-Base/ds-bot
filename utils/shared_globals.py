import os
from pathlib import Path

from openai import AsyncOpenAI

BOT_ROOT_DIR = Path(__file__).parents[1]
BOT_AI_CLIENT: AsyncOpenAI = None  # type: ignore # Похуй.


def init_clients():
    global BOT_AI_CLIENT

    BOT_AI_CLIENT = AsyncOpenAI(
        api_key=os.environ["time_web_api_key"],
        base_url="https://api.timeweb.ai/v1",
    )


__all__ = [
    "BOT_ROOT_DIR",
    "BOT_AI_CLIENT",
    "init_clients",
]
