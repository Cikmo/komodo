import logging
from enum import Enum


class LogLevel(Enum):
    """Enumeration of logging levels."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def setup_logging(level: LogLevel = LogLevel.DEBUG):
    """Set up logging configuration."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level.value)
