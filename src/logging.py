import logging
from enum import Enum
from src.settings import get_settings


class LogLevel(Enum):
    """Enumeration of logging levels."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class StreamFormatter(logging.Formatter):
    """Stream logging format."""

    GREY = "\033[1;30m"
    MAGENTA = "\033[1;35m"
    RESET = "\033[0m"
    FORMATS = {
        logging.INFO: f"{GREY}%(asctime)s{RESET} \033[1;34m%(levelname)-8s\033[0m {MAGENTA}%(name)s{RESET} %(message)s",
        logging.DEBUG: f"{GREY}%(asctime)s{RESET} \033[1;35m%(levelname)-8s\033[0m {MAGENTA}%(name)s{RESET} %(message)s",
        logging.WARNING: f"{GREY}%(asctime)s{RESET} \033[1;33m%(levelname)-8s\033[0m {MAGENTA}%(name)s{RESET} %(message)s",
        logging.ERROR: f"{GREY}%(asctime)s{RESET} \033[1;31m%(levelname)-8s\033[0m {MAGENTA}%(name)s{RESET} %(message)s",
        logging.CRITICAL: f"{GREY}%(asctime)s{RESET} \033[1;41m%(levelname)-8s\033[0m {MAGENTA}%(name)s{RESET} %(message)s",
    }

    def format(self, record: logging.LogRecord):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


class FileFormatter(logging.Formatter):
    """File logging format."""

    FORMATS = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def format(self, record: logging.LogRecord):
        formatter = logging.Formatter(self.FORMATS, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logging():
    """Set up logging configuration."""
    settings = get_settings()

    root_logger = logging.getLogger()
    discord_logger = logging.getLogger("discord")

    root_logger.setLevel(settings.logging.stream_level_komodo)
    discord_logger.setLevel(settings.logging.stream_level_discord)

    ch = logging.StreamHandler()
    ch.setFormatter(StreamFormatter())

    root_logger.addHandler(ch)
