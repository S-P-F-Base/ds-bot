import logging

from colorama import Fore, Style

LEVEL_COLORS = {
    logging.DEBUG: Fore.CYAN,
    logging.INFO: Fore.GREEN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
}


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        levelname = record.levelname
        color = LEVEL_COLORS.get(record.levelno, "")
        colored_level = f"{color}{levelname:<8}{Style.RESET_ALL}"

        asctime = self.formatTime(record, self.datefmt)

        plain_prefix = f"{asctime} [{levelname:<8}] "
        prefix_len = len(plain_prefix)

        colored_prefix = f"{asctime} [{colored_level}] "

        message = record.getMessage()
        lines = message.split("\n")

        result = [f"{colored_prefix}{lines[0]}"] if lines else []
        for line in lines[1:]:
            result.append(" " * prefix_len + line)

        if record.exc_info:
            tb = self.formatException(record.exc_info)
            result.append(tb)

        return "\n".join(result)


for lib in logging.root.manager.loggerDict:
    logging.getLogger(lib).disabled = True

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = ColoredFormatter(
    fmt="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

__all__ = ["logger"]
