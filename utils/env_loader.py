import os

from .shared_globals import BOT_ROOT_DIR


def load_env():
    dump = (BOT_ROOT_DIR / ".env").read_text().strip()
    for line in dump.splitlines():
        if line.startswith("#"):
            continue

        key, value = line.split("=")
        if not key:
            continue

        value: str = value.split("#", 1)[0]

        os.environ[key.lower().strip()] = value.strip()


__all__ = ["load_env"]
