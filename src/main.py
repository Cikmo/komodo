"""
Main module of the application.
"""

import asyncio
import logging
import os

from src.settings import load_or_initialize_settings

if os.name != "nt":
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logger = logging.getLogger(__name__)


def main():
    """The entry point of the application."""

    settings = load_or_initialize_settings("settings.json")

    print(settings)
