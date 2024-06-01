"""
This module contains the logging configuration for the bot.
"""

import logging
from enum import Enum

from src.config.settings import get_settings


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
        logging.INFO: get_settings().logging.stream.format_info,
        logging.DEBUG: get_settings().logging.stream.format_debug,
        logging.WARNING: get_settings().logging.stream.format_warning,
        logging.ERROR: get_settings().logging.stream.format_error,
        logging.CRITICAL: get_settings().logging.stream.format_critical,
    }

    def format(self, record: logging.LogRecord):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(
            log_fmt, datefmt=get_settings().logging.stream.datefmt
        )
        return formatter.format(record)


class FileFormatter(logging.Formatter):
    """File logging format."""

    FORMATS = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def format(self, record: logging.LogRecord):
        formatter = logging.Formatter(
            self.FORMATS, datefmt=get_settings().logging.file.datefmt
        )
        return formatter.format(record)


def setup_logging():
    """Set up logging configuration."""
    settings = get_settings()

    root_logger = logging.getLogger()
    discord_logger = logging.getLogger("discord")

    root_logger.setLevel(settings.logging.stream.level)
    discord_logger.setLevel(settings.logging.stream.level_discord)

    ch = logging.StreamHandler()
    ch.setFormatter(StreamFormatter())

    root_logger.addHandler(ch)
