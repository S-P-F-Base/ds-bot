from functools import cache

from .shared_globals import BOT_ROOT_DIR


@cache
def get_system_prompt() -> str:
    return (BOT_ROOT_DIR / "sys_promt.txt").read_text().strip()


__all__ = ["get_system_prompt"]
