import os
from pathlib import Path

from openai import AsyncOpenAI

from .memory_db import MemoryDB

BOT_ROOT_DIR = Path(__file__).parents[1]
BOT_AI_CLIENT: AsyncOpenAI = None  # type: ignore
BOT_MEMORY_DB: MemoryDB = None  # type: ignore


def init_clients():
    global BOT_AI_CLIENT, BOT_MEMORY_DB

    BOT_AI_CLIENT = AsyncOpenAI(
        api_key=os.environ["time_web_api_key"],
        base_url="https://api.timeweb.ai/v1",
    )
    BOT_MEMORY_DB = MemoryDB()


__all__ = [
    "BOT_AI_CLIENT",
    "BOT_MEMORY_DB",
    "BOT_ROOT_DIR",
    "init_clients",
]
